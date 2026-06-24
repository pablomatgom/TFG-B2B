from __future__ import annotations

from typing import Any

import pandas as pd

# ─── Cumplimiento de lead time por categoría de producto ─────────────────────

_Q_LEAD_TIME = """
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
"""

# ─── Facturas individuales de un proveedor (drill-down de exposición) ─────────

_Q_SUPPLIER_PAIR_OVERDUE = """
    MATCH (sup:Company {legal_name: $supplier_name})-[:ISSUES]->(doc:Document {doc_type: 'INVOICE', status: 'OVERDUE'})
    MATCH (doc)-[:SENT_TO]->(buyer:Company {legal_name: $buyer_name})
    RETURN
        doc.document_id                                         AS document_id,
        buyer.legal_name                                        AS buyer,
        round(toFloat(doc.gross_amount), 2)                     AS gross_amount,
        doc.status                                              AS status,
        toInteger(doc.payment_terms_days)                       AS payment_terms_days,
        toString(doc.due_date)                                  AS due_date,
        toString(doc.issue_date)                                AS issue_date,
        doc.discrepancy_flag                                    AS discrepancy_flag
    ORDER BY gross_amount DESC
"""

_Q_SUPPLIER_INVOICES = """
    MATCH (sup:Company {legal_name: $supplier_name})-[:ISSUES]->(doc:Document {doc_type: 'INVOICE'})
    WHERE doc.payment_terms_days IS NOT NULL AND doc.gross_amount IS NOT NULL
    MATCH (doc)-[:SENT_TO]->(buyer:Company)
    RETURN
        doc.document_id                                         AS document_id,
        buyer.legal_name                                        AS buyer,
        round(toFloat(doc.gross_amount), 2)                     AS gross_amount,
        doc.status                                              AS status,
        toInteger(doc.payment_terms_days)                       AS payment_terms_days,
        toString(doc.due_date)                                  AS due_date,
        toString(doc.issue_date)                                AS issue_date,
        doc.discrepancy_flag                                    AS discrepancy_flag
    ORDER BY gross_amount DESC
"""

# ─── Exposición financiera por proveedor (facturas pendientes de pago) ────────

_Q_PAYMENT_EXPOSURE = """
    MATCH (sup:Company)-[:ISSUES]->(doc:Document {doc_type: 'INVOICE'})
    WHERE doc.payment_terms_days IS NOT NULL AND doc.gross_amount IS NOT NULL
    WITH sup,
         sum(toFloat(doc.gross_amount))        AS total_exposure,
         avg(toFloat(doc.payment_terms_days))  AS avg_payment_days,
         count(doc)                            AS invoice_count
    OPTIONAL MATCH (sup)-[s:SUPPLIES]->()
    WITH sup.legal_name AS supplier,
         total_exposure, avg_payment_days, invoice_count,
         avg(toFloat(s.payment_terms_agreed))  AS avg_agreed_days
    ORDER BY total_exposure DESC
    RETURN supplier,
           round(total_exposure, 2)                              AS total_exposure_eur,
           round(avg_payment_days, 1)                            AS avg_payment_days,
           round(coalesce(avg_agreed_days, avg_payment_days), 1) AS avg_agreed_days,
           invoice_count
"""

# ─── Exposición por facturas vencidas (status = OVERDUE) por par proveedor-comprador ─

_Q_OVERDUE_EXPOSURE = """
    MATCH (sup:Company)-[:ISSUES]->(doc:Document {doc_type: 'INVOICE', status: 'OVERDUE'})
    MATCH (doc)-[:SENT_TO]->(buyer:Company)
    WITH sup, buyer,
         count(doc)                           AS overdue_invoices,
         sum(toFloat(doc.gross_amount))       AS total_overdue_eur,
         avg(toFloat(doc.payment_terms_days)) AS avg_payment_days
    OPTIONAL MATCH (sup)-[s:SUPPLIES]->(buyer)
    WITH sup.legal_name AS supplier, buyer.legal_name AS buyer,
         overdue_invoices, total_overdue_eur, avg_payment_days,
         avg(toFloat(s.payment_terms_agreed)) AS avg_agreed_days
    ORDER BY total_overdue_eur DESC
    RETURN supplier, buyer, overdue_invoices,
           round(total_overdue_eur, 2)                              AS total_overdue_eur,
           round(avg_payment_days, 1)                               AS avg_payment_days,
           round(coalesce(avg_agreed_days, avg_payment_days), 1)    AS avg_agreed_days
"""

# ─── Concentración de riesgo en proveedores dominantes ───────────────────────

_Q_CONCENTRATION_TOTAL = "MATCH ()-[:SUPPLIES]->() RETURN count(*) AS total"

_Q_CONCENTRATION_TOP = """
    MATCH (c:Company)-[:SUPPLIES]->()
    WITH c, count(*) AS degree
    ORDER BY degree DESC
    RETURN c.legal_name AS name, degree
"""

# ─── Riesgo geográfico agregado por Comunidad Autónoma ───────────────────────

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


class OperationalMixin:
    """Cumplimiento operativo, concentración de riesgo y distribución geográfica."""

    def get_supplier_pair_overdue_invoices(self, supplier_name: str, buyer_name: str) -> pd.DataFrame:
        """Devuelve las facturas OVERDUE entre un par proveedor-comprador concreto."""
        return pd.DataFrame(self._fetch_data(_Q_SUPPLIER_PAIR_OVERDUE, supplier_name=supplier_name, buyer_name=buyer_name))

    def get_supplier_invoices(self, supplier_name: str) -> pd.DataFrame:
        """Devuelve las facturas individuales que componen la exposición financiera de un proveedor.

        Args:
            supplier_name: Razón social exacta del proveedor (``Company.legal_name``).

        Returns:
            DataFrame ordenado por ``gross_amount`` descendente con las columnas:

                | Columna | Tipo | Descripción |
                |---|---|---|
                | ``document_id`` | str | Identificador único de la factura |
                | ``buyer`` | str | Razón social del comprador receptor |
                | ``gross_amount`` | float | Importe bruto de la factura (€) |
                | ``status`` | str | Estado del documento (``PENDING / PARTIAL / OVERDUE / PAID``) |
                | ``payment_terms_days`` | int | Plazo de pago acordado en la factura (días) |
                | ``due_date`` | str | Fecha de vencimiento (ISO 8601) |
                | ``issue_date`` | str | Fecha de emisión (ISO 8601) |
                | ``discrepancy_flag`` | bool | Si la factura tiene una discrepancia activa |
        """
        return pd.DataFrame(self._fetch_data(_Q_SUPPLIER_INVOICES, supplier_name=supplier_name))

    def get_lead_time_compliance(self) -> pd.DataFrame:
        """Calcula el retraso medio de entrega respecto al baseline por categoría de producto.

        ``avg_delay_days > 0`` indica que los envíos llegan tarde de media en esa categoría.

        Returns:
            DataFrame ordenado por ``avg_delay_days`` descendente con las columnas:

                | Columna | Tipo | Descripción |
                |---|---|---|
                | ``category`` | str | Categoría de producto |
                | ``avg_delay_days`` | float | Retraso medio respecto al baseline (días) |
                | ``sample`` | int | Documentos con lead time medible |
                | ``late_count`` | int | Entregas que superaron el plazo base |
                | ``late_pct`` | float | Porcentaje de entregas tardías (%) |
        """
        return pd.DataFrame(self._fetch_data(_Q_LEAD_TIME))

    def get_payment_terms_exposure(self) -> pd.DataFrame:
        """Calcula la exposición financiera total por proveedor basada en facturas emitidas.

        Cruza el plazo de pago real de las facturas con el plazo acordado contractualmente
        en las aristas ``SUPPLIES`` para detectar desviaciones sistemáticas.

        Returns:
            DataFrame ordenado por ``total_exposure_eur`` descendente con las columnas:

                | Columna | Tipo | Descripción |
                |---|---|---|
                | ``supplier`` | str | Razón social del proveedor |
                | ``total_exposure_eur`` | float | Suma de importes brutos de facturas (€) |
                | ``avg_payment_days`` | float | Plazo de pago medio real de las facturas (días) |
                | ``avg_agreed_days`` | float | Plazo de pago medio acordado en contratos (días) |
                | ``invoice_count`` | int | Número de facturas analizadas |
        """
        return pd.DataFrame(self._fetch_data(_Q_PAYMENT_EXPOSURE))

    def get_overdue_exposure(self) -> pd.DataFrame:
        """Calcula la exposición financiera real por facturas vencidas desglosada por par proveedor-comprador.

        Puede devolver un DataFrame vacío si el grafo no contiene facturas en estado ``OVERDUE``.

        Returns:
            DataFrame ordenado por ``total_overdue_eur`` descendente con las columnas:

                | Columna | Tipo | Descripción |
                |---|---|---|
                | ``supplier`` | str | Razón social del proveedor emisor |
                | ``buyer`` | str | Razón social del comprador receptor |
                | ``overdue_invoices`` | int | Facturas vencidas entre este par |
                | ``total_overdue_eur`` | float | Importe total vencido (€) |
                | ``avg_payment_days`` | float | Plazo de pago medio real (días) |
                | ``avg_agreed_days`` | float | Plazo de pago medio acordado en contrato (días) |
        """
        return pd.DataFrame(self._fetch_data(_Q_OVERDUE_EXPOSURE))

    def get_supplier_risk_concentration(self) -> dict[str, Any]:
        """Calcula la concentración de riesgo estructural: qué porcentaje del total de enlaces SUPPLIES acaparan los mayores proveedores.

        Un ``concentration_pct`` alto indica dependencia peligrosa de pocos actores clave.
        Ejecuta dos consultas en la misma sesión: total de aristas y top-N por grado de salida.

        Returns:
            Diccionario con las claves:

                | Clave | Tipo | Descripción |
                |---|---|---|
                | ``total_supplies_edges`` | int | Total de aristas SUPPLIES en el grafo |
                | ``top_n`` | int | Número de proveedores en el top |
                | ``concentration_pct`` | float | % del total de aristas acaparadas por el top-N |
                | ``top_suppliers`` | list[dict] | Lista ``[{name, degree, share_pct}, …]`` |
        """
        with self._driver.session(database=self.neo4j_database) as s:
            total_row   = s.run(_Q_CONCENTRATION_TOTAL).single()
            total       = int(total_row["total"]) if total_row else 0
            top_records = s.run(_Q_CONCENTRATION_TOP).data()

        top_degree_sum = sum(int(r["degree"]) for r in top_records)
        top_suppliers = [
            {
                "name":      r["name"],
                "degree":    int(r["degree"]),
                "share_pct": round(int(r["degree"]) / total * 100, 2) if total else 0,
            }
            for r in top_records
        ]
        return {
            "total_supplies_edges": total,
            "top_n":                len(top_records),
            "concentration_pct":    round(top_degree_sum / total * 100, 2) if total else 0,
            "top_suppliers":        top_suppliers,
        }

    def get_geographic_risk(self) -> pd.DataFrame:
        """Agrega el riesgo por región (Comunidad Autónoma) combinando discrepancia y fiabilidad media.

        Solo incluye regiones con al menos una factura emitida por proveedores activos.

        Returns:
            DataFrame ordenado por ``discrepancy_pct`` descendente con las columnas:

                | Columna | Tipo | Descripción |
                |---|---|---|
                | ``region`` | str | Comunidad Autónoma |
                | ``supplier_count`` | int | Número de proveedores activos en la región |
                | ``avg_reliability`` | float | Fiabilidad media contractual de los proveedores (0–1) |
                | ``total_invoices`` | int | Total de facturas emitidas por proveedores de la región |
                | ``discrepancy_pct`` | float | Tasa de facturas con discrepancia en la región (%) |
        """
        return pd.DataFrame(self._fetch_data(_Q_GEOGRAPHIC_RISK))