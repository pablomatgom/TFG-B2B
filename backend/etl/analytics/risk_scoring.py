from __future__ import annotations

from typing import Any

import pandas as pd

# ─── Recomendación de nuevos proveedores para un comprador (fragilidad) ──────
# Candidatos que:
#   (a) venden categorías de producto que el comprador ya aprovisiona, O
#   (b) suministran a compradores del mismo sector/región que el comprador objetivo.
# Ordenados por fiabilidad media y grado de suministro existente.

_Q_BUYER_SUPPLIER_RECOMMENDATIONS = """
    MATCH (buyer:Company {legal_name: $buyer_name})
    OPTIONAL MATCH (buyer)<-[:SUPPLIES]-(cur:Company)-[:SELLS]->(p:Product)
    WITH buyer, collect(DISTINCT p.category) AS sourced_cats

    MATCH (pot:Company)
    WHERE pot.node_role IN ['SUPPLIER', 'HYBRID']
      AND pot.legal_name <> $buyer_name
      AND NOT (pot)-[:SUPPLIES]->(buyer)

    OPTIONAL MATCH (pot)-[:SELLS]->(cp:Product)
    WHERE cp.category IN sourced_cats
    WITH buyer, sourced_cats, pot, count(DISTINCT cp) AS cat_overlap

    OPTIONAL MATCH (pot)-[:SUPPLIES]->(proxy:Company)
    WHERE proxy.region = buyer.region
       OR proxy.industry_code = buyer.industry_code
    WITH buyer, pot, cat_overlap, count(DISTINCT proxy) AS proximity_count

    WHERE cat_overlap > 0 OR proximity_count > 0

    OPTIONAL MATCH (pot)-[es:SUPPLIES]->()
    WITH pot, cat_overlap, proximity_count,
         count(DISTINCT es)              AS supply_degree,
         round(avg(es.reliability_score), 3) AS avg_reliability

    RETURN pot.legal_name           AS supplier,
           pot.region               AS region,
           pot.size_band            AS size_band,
           pot.industry_code        AS industry_code,
           supply_degree,
           coalesce(avg_reliability, 0.0) AS avg_reliability,
           cat_overlap,
           proximity_count
    ORDER BY avg_reliability DESC, supply_degree DESC
    LIMIT 20
"""

# ─── Contratos individuales de un proveedor (drill-down por arista SUPPLIES) ──

_Q_SUPPLIER_CONTRACTS = """
    MATCH (sup:Company {legal_name: $supplier_name})-[s:SUPPLIES]->(buyer:Company)
    RETURN
        buyer.legal_name                                AS buyer,
        buyer.region                                    AS buyer_region,
        s.contract_type                                 AS contract_type,
        s.is_exclusive_supplier                         AS is_exclusive,
        round(s.reliability_score, 3)                   AS reliability_score,
        toInteger(s.payment_terms_agreed)               AS payment_terms_days,
        round(toFloat(coalesce(s.agreed_volume_baseline, 0)), 2) AS agreed_volume_eur,
        toString(s.since_date)                          AS since_date
    ORDER BY reliability_score ASC
"""

# ─── Desglose de contratos por proveedor: tipos, exclusividad y fiabilidad ────

_Q_CONTRACT_DETAIL = """
    MATCH (sup:Company)-[s:SUPPLIES]->(buyer:Company)
    WITH sup.legal_name                                                         AS supplier,
        sup.region                                                              AS region,
        count(s)                                                                AS total_contracts,
        collect(DISTINCT s.contract_type)                                       AS contract_types,
        count(CASE WHEN s.is_exclusive_supplier = true THEN 1 END)              AS exclusive_contracts,
        round(avg(s.reliability_score), 3)                                      AS avg_reliability,
        round(avg(s.payment_terms_agreed), 0)                                   AS avg_payment_terms_days
    RETURN supplier, region, total_contracts, contract_types,
           exclusive_contracts,
           round(toFloat(exclusive_contracts) / total_contracts * 100, 1)       AS exclusive_pct,
           avg_reliability,
           avg_payment_terms_days
    ORDER BY total_contracts DESC
"""

# ─── Fragilidad del comprador: % del volumen de compra controlado por su proveedor principal ─

_Q_BUYER_FRAGILITY = """
    MATCH (buyer:Company)<-[s:SUPPLIES]-(sup:Company)
    WITH buyer, sup, s.agreed_volume_baseline   AS vol
    WITH buyer,
        count(DISTINCT sup)                     AS supplier_count,
        sum(vol)                                AS total_volume,
        max(vol)                                AS top_volume
    WHERE supplier_count > 0
    
    OPTIONAL MATCH (buyer)<-[:SENT_TO]-(ov:Document {doc_type: 'INVOICE', status: 'OVERDUE'})
    WITH buyer, supplier_count, total_volume, top_volume,
        count(ov)                                                       AS overdue_received,
        round(sum(coalesce(toFloat(ov.gross_amount), 0)), 2)            AS overdue_eur
    
    RETURN buyer.legal_name                                             AS buyer,
           buyer.node_role                                              AS node_role,
           buyer.region                                                 AS region,
           supplier_count,
           round(
               CASE WHEN total_volume > 0
                    THEN toFloat(top_volume) / total_volume * 100
                    ELSE 0 END, 2)                                      AS top_supplier_pct,
           round(total_volume, 0)                                       AS total_volume_eur,
           overdue_received,
           overdue_eur
    ORDER BY top_supplier_pct DESC
"""

# ─── Perfil agregado de la red de contratos SUPPLIES ─────────────────────────

_Q_CONTRACT_TYPES = """
    MATCH ()-[s:SUPPLIES]->()
    RETURN s.contract_type AS contract_type, 
        count(s) AS cnt
"""

_Q_CONTRACT_STATS = """
    MATCH ()-[s:SUPPLIES]->()
    RETURN round(avg(s.reliability_score), 4)           AS avg_reliability_score,
            round(avg(s.payment_terms_agreed), 1)       AS avg_payment_terms_days,
            round(
               toFloat(count(CASE WHEN s.is_exclusive_supplier = true THEN 1 END))
               / count(s) * 100, 2
            )                                           AS exclusivity_pct
"""

_Q_CONTRACT_AGE = """
    MATCH ()-[s:SUPPLIES]->()
    WHERE s.since_date IS NOT NULL
    RETURN round(avg(duration.inDays(s.since_date, date()).days), 0) AS avg_contract_age_days
"""


class ScoringMixin:
    """Scoring compuesto de riesgo proveedor, fragilidad de comprador y perfil contractual."""

    def get_buyer_supplier_recommendations(self, buyer_name: str) -> pd.DataFrame:
        """Recomienda nuevos proveedores para un comprador basándose en coincidencia de categorías y proximidad.

        Identifica candidatos potenciales bajo dos criterios complementarios:

        - **Coincidencia de categoría**: proveedores que venden categorías de producto que el
          comprador ya aprovisiona con sus proveedores actuales.
        - **Proximidad sectorial/geográfica**: proveedores que ya abastecen a compradores
          de la misma región o sector que el comprador objetivo.

        Args:
            buyer_name: Razón social exacta del comprador (``Company.legal_name``).

        Returns:
            DataFrame con hasta 20 candidatos, ordenado por ``avg_reliability DESC`` y
            ``supply_degree DESC``, con las columnas:

                | Columna | Tipo | Descripción |
                |---|---|---|
                | ``supplier`` | str | Razón social del proveedor candidato |
                | ``region`` | str | Comunidad Autónoma del proveedor |
                | ``size_band`` | str | Categoría de tamaño (micro / pyme / mid / enterprise) |
                | ``industry_code`` | str | Código NACE del proveedor |
                | ``supply_degree`` | int | Número total de relaciones ``SUPPLIES`` activas |
                | ``avg_reliability`` | float | Fiabilidad media contractual (0–1) |
                | ``cat_overlap`` | int | Nº de categorías de producto coincidentes |
                | ``proximity_count`` | int | Nº de compradores próximos ya abastecidos |

        Note:
            Un proveedor aparece en el resultado si cumple al menos uno de los dos criterios
            (``cat_overlap > 0 OR proximity_count > 0``). Los proveedores que ya abastecen
            directamente al comprador quedan excluidos.
        """
        return pd.DataFrame(self._fetch_data(_Q_BUYER_SUPPLIER_RECOMMENDATIONS, buyer_name=buyer_name))

    def get_supplier_contracts(self, supplier_name: str) -> pd.DataFrame:
        """Devuelve el detalle de cada arista SUPPLIES individual de un proveedor dado.

        Args:
            supplier_name: Razón social exacta del proveedor (``Company.legal_name``).

        Returns:
            DataFrame con una fila por relación ``SUPPLIES`` y las columnas:

                | Columna | Tipo | Descripción |
                |---|---|---|
                | ``buyer`` | str | Razón social del comprador |
                | ``buyer_region`` | str | Comunidad Autónoma del comprador |
                | ``contract_type`` | str | Tipo de contrato (``FRAME / ANNUAL / SPOT``) |
                | ``is_exclusive`` | bool | Si el proveedor es exclusivo en esta relación |
                | ``reliability_score`` | float | Fiabilidad contractual individual (0–1) |
                | ``payment_terms_days`` | int | Plazo de pago acordado (días) |
                | ``agreed_volume_eur`` | float | Volumen de suministro acordado (€) |
                | ``since_date`` | str | Fecha de inicio del contrato |
        """
        return pd.DataFrame(self._fetch_data(_Q_SUPPLIER_CONTRACTS, supplier_name=supplier_name))

    def get_contract_detail(self) -> pd.DataFrame:
        """Desglosa los contratos SUPPLIES activos por proveedor con tipos, exclusividad y fiabilidad.

        Returns:
            DataFrame ordenado por total de contratos descendente con las columnas:

                | Columna | Tipo | Descripción |
                |---|---|---|
                | ``supplier`` | str | Razón social del proveedor |
                | ``region`` | str | Comunidad Autónoma del proveedor |
                | ``total_contracts`` | int | Número de relaciones SUPPLIES activas |
                | ``contract_types`` | list[str] | Tipos de contrato distintos (``FRAME / ANNUAL / SPOT``) |
                | ``exclusive_contracts`` | int | Contratos con exclusividad de proveedor |
                | ``exclusive_pct`` | float | Porcentaje de contratos exclusivos (%) |
                | ``avg_reliability`` | float | Fiabilidad media contractual (0-1) |
                | ``avg_payment_terms_days`` | float | Plazo de pago medio acordado (días) |
        """
        return pd.DataFrame(self._fetch_data(_Q_CONTRACT_DETAIL))

    def compute_supplier_risk_score(self) -> pd.DataFrame:
        r"""Calcula el índice de riesgo compuesto por proveedor en escala 0-100 (mayor = más riesgo).

        Delega en ``get_cross_dimensional_suppliers`` y devuelve una proyección reducida
        con únicamente las columnas de scoring. La fórmula del índice es:

        $$risk\_score = (\text{discrepancy_pct} \times 0.55) + (\text{late_pct} \times 0.45)$$

        Returns:
            DataFrame ordenado por ``risk_score`` descendente con las columnas:

                | Columna | Tipo | Descripción |
                |---|---|---|
                | ``supplier`` | str | Razón social del proveedor |
                | ``avg_reliability`` | float | Fiabilidad media de sus relaciones SUPPLIES (0-1) |
                | ``discrepancy_pct`` | float | Porcentaje de facturas con discrepancia (%) |
                | ``late_pct`` | float | Porcentaje de entregas tardías vs. baseline (%) |
                | ``supply_degree`` | int | Número de relaciones SUPPLIES activas |
                | ``risk_score`` | float | Puntuación de riesgo compuesto (0-100) |
        """
        df = self.get_cross_dimensional_suppliers()
        if df.empty:
            return pd.DataFrame()
        return (
            df[["supplier", "avg_reliability", "discrepancy_pct",
                "late_pct", "supply_degree", "risk_score", "overdue_count", "overdue_eur"]]
            .sort_values("risk_score", ascending=False)
            .reset_index(drop=True)
        )

    def get_buyer_fragility(self) -> pd.DataFrame:
        """Evalúa la fragilidad estructural de cada comprador por dependencia de su proveedor principal.

        Calcula qué porcentaje del volumen de compra total está concentrado en el proveedor de mayor
        volumen (``top_supplier_pct``). Incluye la exposición por facturas vencidas recibidas para identificar 
        compradores con doble vulnerabilidad estructural y financiera. 

        Returns:
            DataFrame ordenado por ``top_supplier_pct`` descendente con las columnas:

                | Columna | Tipo | Descripción |
                |---|---|---|
                | ``buyer`` | str | Razón social del comprador |
                | ``node_role`` | str | Rol en la red (``BUYER / HYBRID``) |
                | ``region`` | str | Comunidad Autónoma del comprador |
                | ``supplier_count`` | int | Número de proveedores distintos |
                | ``top_supplier_pct`` | float | % del volumen total aportado por el proveedor principal |
                | ``total_volume_eur`` | float | Volumen total de compra estimado (€) |
                | ``overdue_received`` | int | Facturas vencidas recibidas en estado ``OVERDUE`` |
                | ``overdue_eur`` | float | Importe total vencido recibido (€) |
        """
        return pd.DataFrame(self._fetch_data(_Q_BUYER_FRAGILITY))

    def get_contract_profile(self) -> dict[str, Any]:
        """Genera el perfil agregado de la red de contratos SUPPLIES con métricas de exclusividad y fiabilidad.

        Ejecuta tres consultas independientes sobre las aristas SUPPLIES para consolidar la 
        distribución macroscópica de tipos de contrato, estadísticas unificadas de pago/fiabilidad 
        y antigüedad temporal media de los vínculos.

        Returns:
            Diccionario con las claves:

                | Clave | Tipo | Descripción |
                |---|---|---|
                | ``contract_type_distribution`` | dict[str, int] | Recuento por tipo (``FRAME / ANNUAL / SPOT``) |
                | ``exclusivity_pct`` | float | % de relaciones con proveedor exclusivo |
                | ``avg_reliability_score`` | float | Fiabilidad media de toda la red (0-1) |
                | ``avg_payment_terms_days`` | float | Plazo de pago medio acordado (días) |
                | ``avg_contract_age_days`` | int | Antigüedad media de los contratos (días) |
        """
        with self._driver.session(database=self.neo4j_database) as session:
            type_rows = session.run(_Q_CONTRACT_TYPES).data()
            stats_row = session.run(_Q_CONTRACT_STATS).single()
            age_row   = session.run(_Q_CONTRACT_AGE).single()

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