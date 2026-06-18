from __future__ import annotations

import pandas as pd

# ─── Overdue invoice exposure: unpaid invoices per supplier-buyer pair ────────

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
    LIMIT 20
    RETURN supplier, buyer, overdue_invoices,
           round(total_overdue_eur, 2)                              AS total_overdue_eur,
           round(avg_payment_days, 1)                               AS avg_payment_days,
           round(coalesce(avg_agreed_days, avg_payment_days), 1)    AS avg_agreed_days
"""


class OperationalMixin:
    """Cumplimiento operativo: lead time, exposición financiera por plazos y facturas vencidas."""

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
        Exposición financiera total (suma de importes de facturas) por proveedor — top-25.
        Indica qué proveedores concentran mayor volumen de deuda pendiente de pago.
        """
        query = """
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
            ORDER BY total_exposure DESC LIMIT 25
            RETURN supplier,
                   round(total_exposure, 2)                             AS total_exposure_eur,
                   round(avg_payment_days, 1)                           AS avg_payment_days,
                   round(coalesce(avg_agreed_days, avg_payment_days), 1) AS avg_agreed_days,
                   invoice_count
        """
        with self._driver.session(database=self.neo4j_database) as s:
            records = s.run(query).data()
        return pd.DataFrame(records)

    def get_overdue_exposure(self) -> pd.DataFrame:
        """
        Exposición financiera real por facturas vencidas (status = OVERDUE).
        Desglosada por par proveedor-comprador, ordenada por importe vencido.
        Puede estar vacía si el grafo no contiene facturas en estado OVERDUE.
        """
        return pd.DataFrame(self._fetch_data(_Q_OVERDUE_EXPOSURE))