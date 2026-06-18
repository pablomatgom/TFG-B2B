from __future__ import annotations

import pandas as pd

# ─── Suppliers appearing simultaneously in multiple risk dimensions ────────────
# Joins reliability, discrepancy rate, and overdue exposure in one traversal.
# risk_score mirrors the same weighted formula used in compute_supplier_risk_score
# (reliability 40 %, discrepancy 35 %, delay capped at 30 d → 25 %) so scores
# are directly comparable across both tabs.

_Q_CROSS_SUPPLIERS = """
    MATCH (sup:Company)-[s:SUPPLIES]->()
    WITH sup,
         round(avg(s.reliability_score), 4) AS avg_reliability,
         count(s)                            AS supply_degree
    OPTIONAL MATCH (sup)-[:ISSUES]->(inv:Document {doc_type: 'INVOICE'})
    WITH sup, avg_reliability, supply_degree,
         count(inv)                                                          AS total_invoices,
         count(CASE WHEN inv.discrepancy_flag = true THEN 1 END)            AS flagged_invoices
    OPTIONAL MATCH (sup)-[:ISSUES]->(doc:Document)-[:CONTAINS]->(p:Product)
    WHERE doc.lead_time_days IS NOT NULL AND p.lead_time_baseline_days IS NOT NULL
    WITH sup, avg_reliability, supply_degree, total_invoices, flagged_invoices,
         coalesce(avg(toFloat(doc.lead_time_days) - toFloat(p.lead_time_baseline_days)), 0.0) AS avg_delay_days
    OPTIONAL MATCH (sup)-[:ISSUES]->(ov:Document {doc_type: 'INVOICE', status: 'OVERDUE'})
    WITH sup, avg_reliability, supply_degree, total_invoices, flagged_invoices, avg_delay_days,
         count(ov)                                                           AS overdue_count,
         round(sum(toFloat(coalesce(ov.gross_amount, 0))), 2)               AS overdue_eur
    WHERE total_invoices >= $min_invoices
    WITH sup.legal_name  AS supplier,
         sup.region      AS region,
         supply_degree,
         total_invoices,
         round(toFloat(flagged_invoices) / total_invoices * 100, 2)         AS discrepancy_pct,
         avg_reliability,
         CASE WHEN avg_delay_days < 0 THEN 0
              WHEN avg_delay_days > 30 THEN 30
              ELSE avg_delay_days END                                        AS delay_capped,
         overdue_count,
         overdue_eur
    RETURN supplier, region, supply_degree, total_invoices, discrepancy_pct,
           round((1 - avg_reliability) * 40
                 + (discrepancy_pct / 100) * 35
                 + (delay_capped / 30) * 25, 2)                             AS risk_score,
           overdue_count,
           overdue_eur
    ORDER BY risk_score DESC, overdue_count DESC
    LIMIT 25
"""

# ─── Buyers with high single-supplier dependency AND overdue receivables ───────

_Q_CROSS_BUYERS = """
    MATCH (buyer:Company)<-[s:SUPPLIES]-(sup:Company)
    WITH buyer, sup, s.agreed_volume_baseline AS vol
    WITH buyer,
         count(DISTINCT sup)  AS supplier_count,
         sum(vol)             AS total_volume,
         max(vol)             AS top_volume
    WHERE supplier_count > 0
    OPTIONAL MATCH (buyer)<-[:SENT_TO]-(ov:Document {doc_type: 'INVOICE', status: 'OVERDUE'})
    WITH buyer, supplier_count, total_volume, top_volume,
         count(ov)                                                           AS overdue_received,
         round(sum(toFloat(coalesce(ov.gross_amount, 0))), 2)               AS overdue_eur
    RETURN buyer.legal_name                                                  AS buyer,
           buyer.region                                                      AS region,
           supplier_count,
           round(
               CASE WHEN total_volume > 0
                    THEN toFloat(top_volume) / total_volume * 100
                    ELSE 0 END, 2)                                           AS top_supplier_pct,
           overdue_received,
           overdue_eur
    ORDER BY top_supplier_pct DESC
    LIMIT 20
"""


class SynthesisMixin:
    """Análisis cruzado multidimensional: proveedores y compradores con riesgo acumulado."""

    def get_cross_dimensional_suppliers(self, min_invoices: int = 3) -> pd.DataFrame:
        """
        Proveedores presentes simultáneamente en múltiples dimensiones de riesgo:
        score compuesto (fiabilidad + discrepancia + retraso) y facturas vencidas.
        Permite identificar actores que son problemáticos en más de un eje de análisis.
        """
        return pd.DataFrame(
            self._fetch_data(_Q_CROSS_SUPPLIERS, min_invoices=min_invoices)
        )

    def get_cross_dimensional_buyers(self) -> pd.DataFrame:
        """
        Compradores con alta dependencia de un único proveedor (top_supplier_pct alto)
        y, simultáneamente, facturas vencidas recibidas (overdue_received > 0).
        Identifica compradores doblemente expuestos: estructural y financieramente.
        """
        return pd.DataFrame(self._fetch_data(_Q_CROSS_BUYERS))