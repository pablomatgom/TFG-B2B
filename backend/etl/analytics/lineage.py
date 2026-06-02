from __future__ import annotations

from typing import Any

import pandas as pd

# ══════════════════════════════════════════════════════════════════════════════
# CYPHER QUERIES
# ══════════════════════════════════════════════════════════════════════════════

# ─── 1. Backward trace: flagged invoice → originating order ──────────────────
# Original method — kept for backward compatibility with run_analyze.py exports.

_Q_DISCREPANCY_LINEAGE = """
    MATCH (invoice:Document {doc_type: 'INVOICE', discrepancy_flag: true})
    MATCH lineage_path = (invoice)-[:FULFILLS*1..5]->(order:Document {doc_type: 'ORDER'})
    MATCH (supplier:Company)-[:ISSUES]->(order)-[:SENT_TO]->(buyer:Company)
    MATCH (order)-[c:CONTAINS]->(product:Product)
    RETURN
        invoice.document_id                     AS factura_id,
        invoice.gross_amount                    AS riesgo_economico,
        order.document_id                       AS pedido_original,
        supplier.legal_name                     AS proveedor,
        buyer.legal_name                        AS afectado,
        collect(DISTINCT product.product_id)    AS id_productos_implicados,
        length(lineage_path)                    AS saltos_topologicos
    ORDER BY invoice.gross_amount DESC
"""

# ─── 2. Exact path extraction ────────────────────────────────────────────────
# Pre-limits invoices by amount before path expansion for performance.
# OPTIONAL MATCH on company nodes retains rows even with orphaned relationships.
# Deduplicates each (invoice, order) pair to the shortest FULFILLS chain.
# cadena_completa: list of {id, tipo, importe, discrepancy, estado, fecha}.

_Q_EXACT_PATH = """
    MATCH (invoice:Document {doc_type: 'INVOICE', discrepancy_flag: true})
    MATCH path = (invoice)-[:FULFILLS*1..5]->(order:Document {doc_type: 'ORDER'})
    OPTIONAL MATCH (supplier:Company)-[:ISSUES]->(order)
    OPTIONAL MATCH (order)-[:SENT_TO]->(buyer:Company)
    WITH invoice, order, supplier, buyer,
         length(path) AS hop_count,
         [n IN nodes(path) | {
             id:          n.document_id,
             tipo:        n.doc_type,
             importe:     n.gross_amount,
             discrepancy: n.discrepancy_flag,
             estado:      n.status,
             fecha:       toString(n.issue_date)
         }] AS cadena_completa
    ORDER BY invoice.document_id, order.document_id, hop_count ASC
    WITH invoice, order, supplier, buyer,
         collect(cadena_completa)[0] AS cadena_completa,
         collect(hop_count)[0]       AS saltos_topologicos
    RETURN
        invoice.document_id                          AS factura_id,
        order.document_id                            AS pedido_original,
        coalesce(supplier.legal_name, 'Desconocido') AS proveedor,
        coalesce(buyer.legal_name, 'Desconocido')    AS afectado,
        cadena_completa                              AS cadena_completa,
        saltos_topologicos                           AS saltos_topologicos,
        invoice.gross_amount                         AS importe_factura,
        order.gross_amount                           AS importe_pedido
    ORDER BY saltos_topologicos DESC, invoice.gross_amount DESC
"""

# ─── 3. Forward traceability: order → all fulfilling documents ───────────────
# Traverses FULFILLS in reverse (documents that point TO an order).
# Captures fulfillment breadth: how many docs cover each order and whether
# any invoice in the chain carries a discrepancy.

_Q_FORWARD = """
    MATCH (order:Document {doc_type: 'ORDER'})
    MATCH (supplier:Company)-[:ISSUES]->(order)-[:SENT_TO]->(buyer:Company)
    OPTIONAL MATCH (fulfiller:Document)-[:FULFILLS*1..5]->(order)
    WITH order, supplier, buyer,
         collect(DISTINCT CASE WHEN fulfiller IS NOT NULL THEN {
             id:          fulfiller.document_id,
             tipo:        fulfiller.doc_type,
             importe:     fulfiller.gross_amount,
             discrepancy: fulfiller.discrepancy_flag,
             estado:      fulfiller.status
         } END) AS documentos_cumplimiento
    WITH order, supplier, buyer, documentos_cumplimiento,
         size(documentos_cumplimiento)    AS total_docs,
         size([d IN documentos_cumplimiento WHERE d.discrepancy = true]) AS docs_con_discrepancia
    WHERE total_docs > 0
    RETURN
        order.document_id                            AS pedido_id,
        coalesce(order.gross_amount, 0)              AS importe_pedido_eur,
        order.status                                 AS estado_pedido,
        supplier.legal_name                          AS proveedor,
        buyer.legal_name                             AS comprador,
        total_docs                                   AS total_docs_cumplimiento,
        docs_con_discrepancia                        AS docs_con_discrepancia,
        documentos_cumplimiento                      AS documentos_cumplimiento
    ORDER BY docs_con_discrepancia DESC, total_docs DESC
"""

# ══════════════════════════════════════════════════════════════════════════════
# MIXIN
# ══════════════════════════════════════════════════════════════════════════════

class LineageMixin:
    """Trazabilidad documental: backward trace, exact path extraction y forward traceability."""

    # ── 1. Backward trace ────────────────────────────────────────────────────
    def get_backward_traceability(self) -> pd.DataFrame:
        """
        Recorre la cadena FULFILLS hacia atrás (hasta 5 saltos) desde facturas
        con discrepancy_flag=true hasta el pedido original. Ordenado por riesgo económico.
        """
        return pd.DataFrame(self._fetch_data(_Q_DISCREPANCY_LINEAGE))

    # ── 2. Exact path extraction ──────────────────────────────────────────────
    def extract_lineage_paths(self) -> pd.DataFrame:
        """
        Extrae la cadena documental completa entre factura discrepante y pedido origen.
        Cada fila incluye `cadena_completa`: lista de nodos con {id, tipo, importe,
        discrepancy, estado, fecha} que permite reconstruir la línea temporal del trazado.
        """
        return pd.DataFrame(self._fetch_data(_Q_EXACT_PATH))

    # ── 3. Forward traceability ───────────────────────────────────────────────
    def get_forward_traceability(self) -> pd.DataFrame:
        """
        Trazabilidad hacia adelante: dado un pedido, lista todos los documentos
        (facturas, albaranes, notas de crédito) que lo cumplen a través de FULFILLS.

        `documentos_cumplimiento` es la lista de documentos vinculados.
        `docs_con_discrepancia` permite identificar pedidos cuya cadena tiene
        al menos un documento en conflicto. Ordenado por conflictividad DESC.
        """
        return pd.DataFrame(self._fetch_data(_Q_FORWARD))
