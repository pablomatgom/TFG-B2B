from __future__ import annotations


import pandas as pd


# ─── Backward trace: flagged invoice → originating order ─────────────────────

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

# ─── Extracción del camino exacto ────────────────────────────────────────────

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

# ─── Trazabilidad hacia adelante: pedido → documentos de cumplimiento ────────

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


class LineageMixin:
    """Trazabilidad documental: backward trace, extracción de camino exacto y forward traceability."""

    def get_backward_traceability(self) -> pd.DataFrame:
        """Recorre la cadena FULFILLS hacia atrás desde facturas con discrepancia hasta el pedido original.

        Recorre inversamente las aristas ``FULFILLS`` con un límite topológico de hasta 5 saltos para 
        conectar directamente un síntoma documental detectado (``discrepancy_flag = true``) con el 
        contrato primario (``ORDER``) que inició el ciclo comercial, aislando el impacto económico expuesto.

        Returns:
            DataFrame con las columnas:

                | Columna | Tipo | Descripción |
                |---|---|---|
                | ``factura_id`` | str | ID de la factura con discrepancia |
                | ``riesgo_economico`` | float | Importe bruto de la factura (€) |
                | ``pedido_original`` | str | ID del pedido raíz de la cadena |
                | ``proveedor`` | str | Razón social del emisor del pedido |
                | ``afectado`` | str | Razón social del comprador receptor |
                | ``id_productos_implicados`` | list[str] | IDs de productos contenidos en el pedido |
                | ``saltos_topologicos`` | int | Longitud del camino FULFILLS recorrido |
        """
        return pd.DataFrame(self._fetch_data(_Q_DISCREPANCY_LINEAGE))

    def extract_lineage_paths(self) -> pd.DataFrame:
        """Extrae la secuencia cronológica e histórica completa entre cada factura discrepante y su pedido raíz.

        Resuelve y aísla el camino transaccional más corto en el grafo para cada par bipartito (factura, pedido). 
        La propiedad mapeada ``cadena_completa`` reconstituye de forma secuencial los estados, fechas e 
        importes de todos los nodos intermedios (como albaranes de entrega ``DELIVERY``), sirviendo de base 
        para una auditoría forense del dato.

        Returns:
            DataFrame ordenado por ``saltos_topologicos DESC`` con las columnas:

                | Columna | Tipo | Descripción |
                |---|---|---|
                | ``factura_id`` | str | ID de la factura con discrepancia |
                | ``pedido_original`` | str | ID del pedido raíz |
                | ``proveedor`` | str | Emisor del pedido (``Desconocido`` si huérfano) |
                | ``afectado`` | str | Receptor del pedido (``Desconocido`` si huérfano) |
                | ``cadena_completa`` | list[dict] | Nodos del recorrido: ``{id, tipo, importe, discrepancy, estado, fecha}`` |
                | ``saltos_topologicos`` | int | Longitud del camino más corto encontrado |
                | ``importe_factura`` | float | Importe bruto de la factura (€) |
                | ``importe_pedido`` | float | Importe bruto del pedido (€) |
        """
        return pd.DataFrame(self._fetch_data(_Q_EXACT_PATH))

    def get_forward_traceability(self) -> pd.DataFrame:
        """Recorre la cadena FULFILLS hacia adelante desde cada pedido para listar sus flujos derivados.

        Inspecciona el flujo aguas abajo de las aristas ``FULFILLS`` a partir de cada nodo ``ORDER``, agregando 
        y agrupando de forma relacional toda la documentación subsiguiente emitida en su cumplimiento. Ordena 
        los resultados según la acumulación de anomalías derivadas para priorizar la fricción operativa en el cliente.

        Returns:
            pd.DataFrame: Matriz de auditoría secuencial ordenada por nivel de conflicto documental. Columnas:

                | Columna | Tipo | Descripción |
                |---|---|---|
                | ``pedido_id`` | str | Código identificador del documento origen ``ORDER`` |
                | ``importe_pedido_eur`` | float | Importe bruto inicial acordado en la orden de compra (€) |
                | ``estado_pedido`` | str | Estado de gestión actual del pedido dentro del sistema ERP |
                | ``proveedor`` | str | Razón social de la compañía proveedora contratada |
                | ``comprador`` | str | Razón social de la compañía cliente solicitante |
                | ``total_docs_cumplimiento`` | int | Volumen total de documentos derivados vinculados por trazabilidad |
                | ``docs_con_discrepancia`` | int | Cantidad absoluta de documentos de la cadena con el flag de error activo |
                | ``documentos_cumplimiento`` | list[dict] | Propiedades de los documentos del flujo: ``{id, tipo, importe, discrepancy, estado}`` |
        """
        return pd.DataFrame(self._fetch_data(_Q_FORWARD))
