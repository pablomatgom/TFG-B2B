from __future__ import annotations

import pandas as pd

_Q_GEOGRAPHIC_RISK = """
    MATCH (sup:Company)
    WHERE sup.region IS NOT NULL AND sup.node_role IN ['SUPPLIER', 'HYBRID']
    OPTIONAL MATCH (sup)-[s:SUPPLIES]->()
    OPTIONAL MATCH (sup)-[:ISSUES]->(inv:Document {doc_type: 'INVOICE'})
    WITH sup.region                                                               AS region,
         count(DISTINCT sup)                                                      AS supplier_count,
         avg(s.reliability_score)                                                 AS avg_reliability,
         count(inv)                                                               AS total_invoices,
         count(CASE WHEN inv.discrepancy_flag = true THEN 1 END)                 AS flagged_invoices
    WHERE total_invoices > 0
    RETURN region,
           supplier_count,
           round(avg_reliability, 3)                                              AS avg_reliability,
           total_invoices,
           round(toFloat(flagged_invoices) / total_invoices * 100, 2)            AS discrepancy_pct
    ORDER BY discrepancy_pct DESC
"""


class GeographicMixin:
    """Distribución geográfica del riesgo documental y de fiabilidad de proveedores."""

    def get_geographic_risk(self) -> pd.DataFrame:
        """
        Riesgo agregado por región (Comunidad Autónoma).
        Combina tasa de discrepancia e índice de fiabilidad media de todos los proveedores
        de cada región. Útil para identificar zonas geográficas de mayor exposición.
        """
        return pd.DataFrame(self._fetch_data(_Q_GEOGRAPHIC_RISK))