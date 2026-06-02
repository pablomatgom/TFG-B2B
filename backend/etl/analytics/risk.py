from __future__ import annotations

from typing import Any

import pandas as pd

# ══════════════════════════════════════════════════════════════════════════════
# CYPHER QUERIES
# ══════════════════════════════════════════════════════════════════════════════

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


class RiskMixin:
    """Analítica avanzada de riesgo operacional y financiero de la red de proveedores."""

    def get_supplier_risk_concentration(self, top_n: int = 10) -> dict[str, Any]:
        """
        Concentración de riesgo: qué % del total de enlaces SUPPLIES acaparan los top-N proveedores.
        Un concentration_pct alto indica dependencia peligrosa de pocos actores.
        """
        q_total = "MATCH ()-[:SUPPLIES]->() RETURN count(*) AS total"
        q_top   = """
            MATCH (c:Company)-[:SUPPLIES]->()
            WITH c, count(*) AS degree
            ORDER BY degree DESC LIMIT $top_n
            RETURN c.legal_name AS name, degree
        """
        with self._driver.session(database=self.neo4j_database) as s:
            total_row   = s.run(q_total).single()
            total       = int(total_row["total"]) if total_row else 0
            top_records = s.run(q_top, top_n=top_n).data()

        top_degree_sum = sum(int(r["degree"]) for r in top_records)
        top_suppliers  = [
            {
                "name":      r["name"],
                "degree":    int(r["degree"]),
                "share_pct": round(int(r["degree"]) / total * 100, 2) if total else 0,
            }
            for r in top_records
        ]
        return {
            "total_supplies_edges": total,
            "top_n":                top_n,
            "concentration_pct":    round(top_degree_sum / total * 100, 2) if total else 0,
            "top_suppliers":        top_suppliers,
        }

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

    def get_lead_time_compliance(self) -> pd.DataFrame:
        """
        Retraso medio vs. baseline por categoría de producto.
        avg_delay_days > 0 significa que los envíos llegan tarde de media.
        late_pct es el porcentaje de entregas que superaron el plazo base del producto.
        """
        query = """
            MATCH (doc:Document)-[:CONTAINS]->(p:Product)
            WHERE doc.lead_time_days IS NOT NULL AND p.lead_time_baseline_days IS NOT NULL
            WITH p.category AS category,
                 avg(toFloat(doc.lead_time_days) - toFloat(p.lead_time_baseline_days)) AS avg_delay,
                 count(doc) AS sample,
                 count(CASE WHEN toFloat(doc.lead_time_days) > toFloat(p.lead_time_baseline_days) THEN 1 END) AS late_count
            RETURN category,
                   round(avg_delay, 2)                          AS avg_delay_days,
                   sample,
                   late_count,
                   round(toFloat(late_count) / sample * 100, 1) AS late_pct
            ORDER BY avg_delay_days DESC
            LIMIT 15
        """
        with self._driver.session(database=self.neo4j_database) as s:
            records = s.run(query).data()
        return pd.DataFrame(records)

    def get_payment_terms_exposure(self) -> pd.DataFrame:
        """
        Exposición financiera total (suma de importes de facturas) por proveedor — top-15.
        Indica qué proveedores concentran mayor volumen de deuda pendiente de pago.
        """
        query = """
            MATCH (sup:Company)-[:ISSUES]->(doc:Document {doc_type: 'INVOICE'})
            WHERE doc.payment_terms_days IS NOT NULL AND doc.gross_amount IS NOT NULL
            WITH sup.legal_name AS supplier,
                 sum(toFloat(doc.gross_amount))        AS total_exposure,
                 avg(toFloat(doc.payment_terms_days))  AS avg_payment_days,
                 count(doc)                            AS invoice_count
            ORDER BY total_exposure DESC LIMIT 15
            RETURN supplier,
                   round(total_exposure, 2)     AS total_exposure_eur,
                   round(avg_payment_days, 1)   AS avg_payment_days,
                   invoice_count
        """
        with self._driver.session(database=self.neo4j_database) as s:
            records = s.run(query).data()
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