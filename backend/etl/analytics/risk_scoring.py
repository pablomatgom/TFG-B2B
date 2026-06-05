from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

# ─── Composite supplier risk score: single-pass join of all three risk dims ───
# Joins reliability (SUPPLIES edge), discrepancy rate (INVOICE docs), and
# avg lead-time delay (Document → Product) in one traversal.
# The $min_invoices filter removes low-sample suppliers before scoring.

_Q_SUPPLIER_RISK_SCORE = """
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
         avg(toFloat(doc.lead_time_days) - toFloat(p.lead_time_baseline_days)) AS avg_delay_days
    WHERE total_invoices >= $min_invoices
    RETURN sup.company_id AS company_id,
           sup.legal_name  AS supplier,
           avg_reliability,
           supply_degree,
           total_invoices,
           round(toFloat(flagged_invoices) / total_invoices * 100, 2) AS discrepancy_pct,
           round(coalesce(avg_delay_days, 0.0), 2)                    AS avg_delay_days
    ORDER BY supplier
"""

# ─── Buyer fragility: % of total inbound volume from single top supplier ──────

_Q_BUYER_FRAGILITY = """
    MATCH (buyer:Company)<-[s:SUPPLIES]-(sup:Company)
    WITH buyer, sup, s.agreed_volume_baseline AS vol
    WITH buyer,
         count(DISTINCT sup)  AS supplier_count,
         sum(vol)             AS total_volume,
         max(vol)             AS top_volume
    WHERE supplier_count > 0
    RETURN buyer.legal_name                                             AS buyer,
           buyer.node_role                                              AS node_role,
           buyer.region                                                 AS region,
           supplier_count,
           round(
               CASE WHEN total_volume > 0
                    THEN toFloat(top_volume) / total_volume * 100
                    ELSE 0 END, 2)                                      AS top_supplier_pct,
           round(total_volume, 0)                                       AS total_volume_eur
    ORDER BY top_supplier_pct DESC
    LIMIT 20
"""


class ScoringMixin:
    """Scoring compuesto de riesgo proveedor, fragilidad de comprador y perfil contractual."""

    def compute_supplier_risk_score(self, min_invoices: int = 3) -> pd.DataFrame:
        """
        Índice de riesgo compuesto por proveedor (0–100, mayor = más riesgo).

        Combina tres dimensiones en una sola pasada Cypher:
          - Fiabilidad de la relación SUPPLIES          (peso 40 %)
          - Tasa de facturas con discrepancia           (peso 35 %)
          - Retraso medio de entrega vs. baseline       (peso 25 %, techo 30 d)

        El scoring final usa NumPy vectorizado sobre el DataFrame resultante.
        Solo se incluyen proveedores con al menos min_invoices facturas emitidas.
        """
        records = self._fetch_data(_Q_SUPPLIER_RISK_SCORE, min_invoices=min_invoices)
        if not records:
            return pd.DataFrame()

        df = pd.DataFrame(records)
        rel   = df["avg_reliability"].to_numpy(dtype=float)
        disc  = df["discrepancy_pct"].to_numpy(dtype=float) / 100
        delay = np.clip(df["avg_delay_days"].to_numpy(dtype=float), 0, 30) / 30

        df["risk_score"] = ((1 - rel) * 40 + disc * 35 + delay * 25).round(2)

        return (
            df[["supplier", "avg_reliability", "discrepancy_pct",
                "avg_delay_days", "supply_degree", "risk_score"]]
            .sort_values("risk_score", ascending=False)
            .head(25)
            .reset_index(drop=True)
        )

    def get_buyer_fragility(self) -> pd.DataFrame:
        """
        Fragilidad del comprador: % del volumen de compra total controlado
        por su proveedor principal (top_supplier_pct).
        Un valor alto indica alta dependencia de un único proveedor.
        Top-20 compradores más expuestos.
        """
        return pd.DataFrame(self._fetch_data(_Q_BUYER_FRAGILITY))

    def get_contract_profile(self) -> dict[str, Any]:
        """
        Perfil estructural de la red de contratos SUPPLIES:
          - contract_type_distribution: recuento por tipo (FRAME / ANNUAL / SPOT)
          - exclusivity_pct:            % de relaciones con proveedor exclusivo
          - avg_reliability_score:      fiabilidad media de toda la red
          - avg_payment_terms_days:     plazo de pago medio acordado
          - avg_contract_age_days:      antigüedad media de los contratos
        """
        q_types = """
            MATCH ()-[s:SUPPLIES]->()
            RETURN s.contract_type AS contract_type, count(s) AS cnt
        """
        q_stats = """
            MATCH ()-[s:SUPPLIES]->()
            RETURN round(avg(s.reliability_score), 4)   AS avg_reliability_score,
                   round(avg(s.payment_terms_agreed), 1) AS avg_payment_terms_days,
                   round(
                       toFloat(count(CASE WHEN s.is_exclusive_supplier = true THEN 1 END))
                       / count(s) * 100, 2
                   ) AS exclusivity_pct
        """
        q_age = """
            MATCH ()-[s:SUPPLIES]->()
            WHERE s.since_date IS NOT NULL
            RETURN round(avg(duration.inDays(s.since_date, date()).days), 0) AS avg_contract_age_days
        """
        with self._driver.session(database=self.neo4j_database) as session:
            type_rows = session.run(q_types).data()
            stats_row = session.run(q_stats).single()
            age_row   = session.run(q_age).single()

        distribution = {
            r["contract_type"]: int(r["cnt"])
            for r in type_rows
            if r["contract_type"]
        }
        return {
            "contract_type_distribution": distribution,
            "exclusivity_pct":        float(stats_row["exclusivity_pct"] or 0)        if stats_row else 0.0,
            "avg_reliability_score":  float(stats_row["avg_reliability_score"] or 0)  if stats_row else 0.0,
            "avg_payment_terms_days": float(stats_row["avg_payment_terms_days"] or 0) if stats_row else 0.0,
            "avg_contract_age_days":  int(age_row["avg_contract_age_days"] or 0)       if age_row else 0,
        }