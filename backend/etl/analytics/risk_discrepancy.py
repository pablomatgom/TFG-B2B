from __future__ import annotations

import pandas as pd

# ─── Commercial impact algebra: per-order Δ€ and billing state ───────────────
# For every order that has at least one fulfilling invoice, computes:
#   delta_eur  = sum(invoiced) − ordered_amount
#   delta_pct  = delta_eur / ordered_amount × 100
#   estado_comercial:
#     SOBREFACTURADO  →  invoiced > ordered × (1 + tolerance/100)
#     SUBFACTURADO    →  invoiced < ordered × (1 - tolerance/100)
#     CONFORME        →  within the tolerance band
# The tolerance band is parametric via $tolerance (default 5.0 %).

_Q_COMMERCIAL_IMPACT = """
    MATCH (order:Document {doc_type: 'ORDER'})
    MATCH (supplier:Company)-[:ISSUES]->(order)-[:SENT_TO]->(buyer:Company)
    OPTIONAL MATCH (invoice:Document {doc_type: 'INVOICE'})-[:FULFILLS*1..5]->(order)
    WITH order, supplier, buyer,
         count(invoice)                                                              AS num_facturas,
         round(sum(toFloat(coalesce(invoice.gross_amount, 0))), 2)                  AS total_facturado,
         count(CASE WHEN invoice.discrepancy_flag = true THEN 1 END)                AS facturas_con_discrepancia,
         round(sum(CASE WHEN invoice.discrepancy_flag = true
                        THEN toFloat(coalesce(invoice.gross_amount, 0))
                        ELSE 0 END), 2)                                             AS importe_en_discrepancia
    WHERE num_facturas > 0
    WITH order, supplier, buyer,
         num_facturas, total_facturado, facturas_con_discrepancia, importe_en_discrepancia,
         toFloat(coalesce(order.gross_amount, 0))                                   AS importe_pedido,
         $tolerance                                                                 AS tol
    RETURN
        order.document_id                                                            AS pedido_id,
        supplier.legal_name                                                          AS proveedor,
        buyer.legal_name                                                             AS comprador,
        round(importe_pedido, 2)                                                     AS importe_pedido_eur,
        total_facturado                                                              AS total_facturado_eur,
        round(total_facturado - importe_pedido, 2)                                  AS delta_eur,
        CASE WHEN importe_pedido > 0
             THEN round((total_facturado - importe_pedido) / importe_pedido * 100, 2)
             ELSE null
        END                                                                          AS delta_pct,
        num_facturas,
        facturas_con_discrepancia,
        importe_en_discrepancia                                                      AS importe_en_discrepancia_eur,
        CASE
            WHEN total_facturado > importe_pedido * (1 + tol / 100) THEN 'SOBREFACTURADO'
            WHEN total_facturado < importe_pedido * (1 - tol / 100) THEN 'SUBFACTURADO'
            ELSE 'CONFORME'
        END                                                                          AS estado_comercial
    ORDER BY abs(total_facturado - importe_pedido) DESC
    LIMIT $limit
"""


class DiscrepancyMixin:
    """Tasa de discrepancias documentales e impacto comercial por pedido."""

    def get_discrepancy_rate_by_supplier(self, min_invoices: int = 5) -> pd.DataFrame:
        """
        Tasa de facturas con discrepancia por proveedor (top-20 más problemáticos).
        Solo incluye proveedores con al menos min_invoices facturas emitidas.
        """
        query = """
            MATCH (sup:Company)-[:ISSUES]->(doc:Document {doc_type: 'INVOICE'})
            WITH sup, count(doc) AS total,
                 count(CASE WHEN doc.discrepancy_flag = true THEN 1 END) AS flagged
            WHERE total >= $min_invoices
            RETURN sup.legal_name AS supplier, total, flagged,
                   round(toFloat(flagged) / total * 100, 2) AS discrepancy_rate_pct
            ORDER BY discrepancy_rate_pct DESC
            LIMIT 20
        """
        with self._driver.session(database=self.neo4j_database) as s:
            records = s.run(query, min_invoices=min_invoices).data()
        return pd.DataFrame(records)

    def compute_commercial_impact(
        self,
        limit: int = 100,
        tolerance_pct: float = 5.0,
    ) -> pd.DataFrame:
        """
        Álgebra de impacto comercial por pedido.

        Calcula la desviación entre el importe acordado en el pedido y la suma
        de facturas que lo cumplen:
          - delta_eur        → diferencia absoluta (positivo = sobrefacturado)
          - delta_pct        → diferencia relativa sobre el importe del pedido
          - estado_comercial → SOBREFACTURADO / SUBFACTURADO / CONFORME

        `tolerance_pct` define la banda de tolerancia bilateral (default ±5 %).
        Ordenado por abs(delta_eur) DESC para priorizar el mayor impacto financiero.
        """
        return pd.DataFrame(
            self._fetch_data(_Q_COMMERCIAL_IMPACT, limit=limit, tolerance=tolerance_pct)
        )