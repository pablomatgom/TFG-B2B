from __future__ import annotations

import pandas as pd

# ─── Proveedores presentes simultáneamente en múltiples dimensiones de riesgo ─

_Q_CROSS_SUPPLIERS = """
     MATCH (sup:Company)-[s:SUPPLIES]->()
     WITH sup,
          round(avg(s.reliability_score), 4)                                    AS avg_reliability,
          count(s)                                                              AS supply_degree
     
     // ── Tasa de discrepancia (solo facturas) ─────────────────────────────
     OPTIONAL MATCH (sup)-[:ISSUES]->(inv:Document {doc_type: 'INVOICE'})
     WITH sup, avg_reliability, supply_degree,
          count(inv)                                                            AS total_invoices,
          count(CASE WHEN inv.discrepancy_flag = true THEN 1 END)               AS flagged_invoices

     // ── Cumplimiento de lead time (vs. baseline de producto) ─────────────
     OPTIONAL MATCH (sup)-[:ISSUES]->(doc:Document)-[:CONTAINS]->(p:Product)
     WHERE doc.lead_time_days IS NOT NULL AND p.lead_time_baseline_days IS NOT NULL
     WITH sup, avg_reliability, supply_degree, total_invoices, flagged_invoices,
          count(doc)                                                                                     AS total_with_baseline,
          count(CASE WHEN toFloat(doc.lead_time_days) > toFloat(p.lead_time_baseline_days) THEN 1 END)   AS late_docs

     // ── Facturas vencidas e importe total vencido ─────────────────────────
     OPTIONAL MATCH (sup)-[:ISSUES]->(ov:Document {doc_type: 'INVOICE', status: 'OVERDUE'})
     WITH sup, avg_reliability, supply_degree, total_invoices, flagged_invoices,
          total_with_baseline, late_docs,
          count(ov)                                                             AS overdue_count,
          round(sum(toFloat(coalesce(ov.gross_amount, 0))), 2)                  AS overdue_eur
     
     // ── Tasas derivadas (de conteos a porcentajes) ────────────────────────
     WITH sup.legal_name                                                        AS supplier,
          sup.region                                                            AS region,
          supply_degree,
          total_invoices,
          round(
               CASE WHEN total_invoices > 0 
                    THEN toFloat(flagged_invoices) / total_invoices * 100        
                    ELSE 0.0 END, 2)                                            AS discrepancy_pct,
          avg_reliability,
          round(
               CASE WHEN total_with_baseline > 0
                    THEN toFloat(late_docs) / total_with_baseline * 100
                    ELSE 0 END, 2)                                              AS late_pct,
          overdue_count,
          overdue_eur
     
     RETURN supplier, region, supply_degree, total_invoices, discrepancy_pct, late_pct,
               round((discrepancy_pct / 100) * 55 + (late_pct / 100) * 45, 2)   AS risk_score,
               avg_reliability,
               overdue_count,
               overdue_eur
     ORDER BY risk_score DESC, overdue_count DESC
"""

class SynthesisMixin:
     """
     Mixin de síntesis analítica para la correlación cruzada de riesgos en la red B2B.

    Agrupa la lógica de negocio encargada de unificar vectores de vulnerabilidad operativa, 
    logística y financiera. Su propósito es exponer de manera global a aquellos actores 
    del sistema que presentan criticidad compuesta en múltiples capas del pipeline.
    """

     def get_cross_dimensional_suppliers(self) -> pd.DataFrame:
          r"""Identifica proveedores simultáneamente problemáticos en múltiples dimensiones de riesgo.

          Cruza en una sola consulta tres ejes operativos y financieros: tasa de discrepancia, 
          tasa de retraso de entrega y volumen de facturas vencidas. El indicador compuesto 
          se calcula por la ecuación:

          $$risk\_score = (\text{discrepancy_pct} \times 0.55) + (\text{late_pct} \times 0.45)$$

          Returns:
               Matriz ordenada de mayor a menor con las siguientes columnas analíticas:

                    | Columna | Tipo | Descripción |
                    |---|---|---|
                    | ``supplier`` | str | Razón social del proveedor |
                    | ``region`` | str | Demarcación geográfica (Comunidad Autónoma) |
                    | ``supply_degree`` | int | Número de relaciones ``SUPPLIES`` activas |
                    | ``total_invoices`` | int | Volumen total de facturas emitidas analizadas |
                    | ``discrepancy_pct`` | float | Porcentaje de facturación con discrepancias documentales |
                    | ``late_pct`` | float | Porcentaje de entregas con retraso sobre el baseline de producto |
                    | ``risk_score`` | float | Puntuación final de riesgo compuesto unificado |
                    | ``avg_reliability`` | float | Reputación media contractual de las relaciones de suministro |
                    | ``overdue_count`` | int | Cantidad absoluta de facturas impagadas en estado de mora |
                    | ``overdue_eur`` | float | Importe económico total acumulado en mora (€) |
          """
          return pd.DataFrame(self._fetch_data(_Q_CROSS_SUPPLIERS))