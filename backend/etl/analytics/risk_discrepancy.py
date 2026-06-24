from __future__ import annotations

import pandas as pd

# ─── Tasa de discrepancia por proveedor ──────────────────────────────────────

_Q_DISCREPANCY_RATE = """
    MATCH (sup:Company)-[:ISSUES]->(doc:Document {doc_type: 'INVOICE'})
    
    WITH sup, count(doc)                                            AS total,
        count(CASE WHEN doc.discrepancy_flag = true THEN 1 END)     AS flagged
    
    RETURN sup.legal_name                                           AS supplier, 
        total, flagged,
        round(toFloat(flagged) / total * 100, 2)                    AS discrepancy_rate_pct
    ORDER BY discrepancy_rate_pct DESC
"""

# ─── Álgebra de impacto comercial: Δ€ y estado de facturación por pedido ──────

_Q_COMMERCIAL_IMPACT = """
    MATCH (order:Document {doc_type: 'ORDER'})
    MATCH (supplier:Company)-[:ISSUES]->(order)-[:SENT_TO]->(buyer:Company)

    // ── Agregación de facturas asociadas por trazabilidad (FULFILLS*1..5) ──
    OPTIONAL MATCH (invoice:Document {doc_type: 'INVOICE'})-[:FULFILLS*1..5]->(order)
    WITH order, supplier, buyer,
        count(invoice)                                                              AS num_facturas,
        round(sum(toFloat(coalesce(invoice.gross_amount, 0))), 2)                   AS total_facturado,
        count(CASE WHEN invoice.discrepancy_flag = true THEN 1 END)                 AS facturas_con_discrepancia,
        round(sum(CASE WHEN invoice.discrepancy_flag = true
                        THEN toFloat(coalesce(invoice.gross_amount, 0))
                        ELSE 0 END), 2)                                             AS importe_en_discrepancia
    WHERE num_facturas > 0

    // ── Importe del pedido y banda de tolerancia paramétrizada ────────────
    WITH order, supplier, buyer,
        num_facturas, total_facturado, facturas_con_discrepancia, importe_en_discrepancia,
        toFloat(coalesce(order.gross_amount, 0))                                    AS importe_pedido,
        $tolerance                                                                  AS tol

    // ── Desviación absoluta/relativa y clasificación comercial ────────────
    RETURN
        order.document_id                                                           AS pedido_id,
        supplier.legal_name                                                         AS proveedor,
        buyer.legal_name                                                            AS comprador,
        round(importe_pedido, 2)                                                    AS importe_pedido_eur,
        total_facturado                                                             AS total_facturado_eur,
        round(total_facturado - importe_pedido, 2)                                  AS delta_eur,
        CASE WHEN importe_pedido > 0
            THEN round((total_facturado - importe_pedido) / importe_pedido * 100, 2)
            ELSE null
        END                                                                         AS delta_pct,
        num_facturas,
        facturas_con_discrepancia,
        importe_en_discrepancia                                                     AS importe_en_discrepancia_eur,
        CASE
            WHEN total_facturado > importe_pedido * (1 + tol / 100) THEN 'SOBREFACTURADO'
            WHEN total_facturado < importe_pedido * (1 - tol / 100) THEN 'SUBFACTURADO'
            ELSE 'CONFORME'
        END                                                                         AS estado_comercial
    ORDER BY abs(total_facturado - importe_pedido) DESC
"""


class DiscrepancyMixin:
    """Tasa de discrepancias documentales e impacto comercial por pedido."""

    def get_discrepancy_rate_by_supplier(self) -> pd.DataFrame:
        """Calcula la tasa de facturas anomalas o con discrepancias agrupadas por proveedor.
        
        Analiza exclusivamente los documentos ``INVOICE`` emitidos por cada proveedor 
        para determinar qué porcentaje del volumen total presenta el flag de error activo 
        (``discrepancy_flag = true``).

        Returns:
            DataFrame ordenada descendentemente por tasa de error:

                | Columna | Tipo | Descripción |
                |---|---|---|
                | ``supplier`` | str | Razón social del proveedor |
                | ``total`` | int | Total de facturas emitidas |
                | ``flagged`` | int | Facturas con discrepancia |
                | ``discrepancy_rate_pct`` | float | Tasa de discrepancia (%) |
        """
        return pd.DataFrame(self._fetch_data(_Q_DISCREPANCY_RATE))

    def compute_commercial_impact(self, tolerance_pct: float = 5.0) -> pd.DataFrame:
        """Calcula la desviación económica entre el importe solicitado y el facturado por cada pedido.

        Recorre el grafo de trazabilidad EDI mediante caminos variables de hasta 5 saltos para 
        consolidar la facturación asociada a cada pedido (ORDER). Calcula el descuadre financiero 
        global y clasifica su estado según la tolerancia bilateral.

        Args:
            tolerance_pct: Banda de tolerancia bilateral en %.
                Pedidos cuyas desviaciones no superen este límite se clasifican como ``CONFORME``.

        Returns:
            DataFrame ordenado por ``abs(delta_eur) DESC`` con las columnas:

                | Columna | Tipo | Descripción |
                |---|---|---|
                | ``pedido_id`` | str | ID del pedido ``ORDER`` |
                | ``proveedor`` | str | Razón social del proveedor |
                | ``comprador`` | str | Razón social del comprador |
                | ``importe_pedido_eur`` | float | Importe acordado en el pedido (€) |
                | ``total_facturado_eur`` | float | Suma de importes de facturas de cumplimiento (€) |
                | ``delta_eur`` | float | Desviación absoluta (positivo = sobrefacturado) (€) |
                | ``delta_pct`` | float | Desviación relativa sobre el importe del pedido (%) |
                | ``num_facturas`` | int | Facturas que cumplen el pedido |
                | ``facturas_con_discrepancia`` | int | Facturas con ``discrepancy_flag = true`` |
                | ``importe_en_discrepancia_eur`` | float | Importe acumulado en facturas con discrepancia (€) |
                | ``estado_comercial`` | str | ``SOBREFACTURADO`` / ``SUBFACTURADO`` / ``CONFORME`` |
        
        Note:
            Aunque el método computa y preclasifica el campo ``estado_comercial`` en el backend 
            usando la tolerancia paramétrica, la arquitectura actual realiza una reclasificación 
            dinámica e interactiva a traves de un *slider* del frontend, recalculando las etiquetas 
            en tiempo real en el cliente sobre la métrica ``delta_pct``.
        """
        return pd.DataFrame(self._fetch_data(_Q_COMMERCIAL_IMPACT, tolerance=tolerance_pct))