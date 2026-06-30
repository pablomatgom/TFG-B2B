from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class GraphMacroStats:
    """Snapshot inmutable de las métricas macroscópicas de la red B2B.

    Attributes:
        node_counts: Nodos por etiqueta Neo4j (``Company``, ``Document``, etc.).
        relationship_counts: Aristas por tipo (``SUPPLIES``, ``ISSUES``, etc.).
        top_suppliers: Top proveedores por grado de salida ``SUPPLIES``.
        top_buyers: Top compradores por grado de entrada ``SUPPLIES``.
        doc_type_counts: Distribución de tipos de documento EDI.
        economic_volume: Volumen bruto, neto e impuesto agregado de facturas.
        document_health: Total de documentos, flagged y tasa de discrepancia global.
        scale_free_metrics: Indicadores de topología scale-free (Gini, hubs, grado).
    """

    node_counts:           dict[str, int]
    relationship_counts:   dict[str, int]
    top_suppliers:         list[dict[str, Any]]
    top_buyers:            list[dict[str, Any]]
    doc_type_counts:       dict[str, int]
    economic_volume:       dict[str, Any]
    document_health:       dict[str, Any]
    scale_free_metrics:    dict[str, Any]


# ─── Estructura del grafo: conteo de nodos y aristas ─────────────────────────

_Q_NODES = (
    "MATCH (n) RETURN labels(n)[0] AS label, count(n) AS total ORDER BY label"
)

_Q_EDGES = (
    "MATCH ()-[r]->() RETURN type(r) AS relationship, count(r) AS total ORDER BY relationship"
)

# ─── Rankings: top proveedores, compradores y distribución documental ─────────

_Q_TOP_SUPPLIERS = """
    MATCH (supplier:Company)-[r:SUPPLIES]->(buyer:Company)
    RETURN supplier.company_id              AS company_id,
            supplier.legal_name             AS legal_name,
            count(r)                        AS supplies_out,
            avg(r.agreed_volume_baseline)   AS avg_agreed_volume
    ORDER BY supplies_out DESC, avg_agreed_volume DESC
"""

_Q_TOP_BUYERS = """
    MATCH (supplier:Company)-[r:SUPPLIES]->(buyer:Company)
    RETURN buyer.company_id                 AS company_id,
            buyer.legal_name                AS legal_name,
            count(r)                        AS supplies_in,
            avg(r.agreed_volume_baseline)   AS avg_agreed_volume
    ORDER BY supplies_in DESC, avg_agreed_volume DESC
"""

_Q_DOC_TYPES = (
    "MATCH (d:Document) RETURN d.doc_type AS doc_type, count(d) AS total ORDER BY total DESC"
)

# ─── Serie temporal mensual de actividad ─────────────────────────────────────
# Seis métricas por mes derivadas del mismo bucket documental:
#   documents          — total de documentos EDI emitidos
#   flagged            — subconjunto con discrepancy_flag = true
#   total_gross_eur    — importe bruto agregado (solo INVOICE)
#   active_companies   — empresas distintas que emitieron documentos
#   active_products    — productos distintos referenciados
#   active_connections — pares proveedor→comprador activos

_Q_TEMPORAL = """
    MATCH (d:Document)-[:Issue_on]->(tb:TimeBucket)
    WITH tb.year                                                                AS year,
        tb.month                                                                AS month,
        count(d)                                                                AS documents,
        count(CASE WHEN d.discrepancy_flag = true THEN 1 END)                   AS flagged,
        round(
            sum(CASE WHEN d.doc_type = 'INVOICE'
                    THEN toFloat(coalesce(d.gross_amount, 0))
                    ELSE 0 END), 2
        )                                                                       AS total_gross_eur,
        collect(d)                                                              AS month_docs
    CALL {
        WITH month_docs
        UNWIND month_docs                                                       AS d
        MATCH (c:Company)-[:ISSUES]->(d)
        RETURN count(DISTINCT c)                                                AS active_companies
    }
    CALL {
        WITH month_docs
        UNWIND month_docs                                                       AS d
        MATCH (d)-[:CONTAINS]->(p:Product)
        RETURN count(DISTINCT p)                                                AS active_products
    }
    CALL {
        WITH month_docs
        UNWIND month_docs                                                       AS d
        MATCH (issuer:Company)-[:ISSUES]->(d)-[:SENT_TO]->(buyer:Company)
        RETURN count(DISTINCT (issuer.company_id + '|' + buyer.company_id))     AS active_connections
    }
    RETURN
        year,
        month,
        documents,
        flagged,
        total_gross_eur,
        active_companies,
        active_products,
        active_connections
    ORDER BY year, month
"""

# ─── Scalar queries ───────────────────────────────────────────────────────────

_Q_DOCUMENT_HEALTH = """
    MATCH (doc:Document)
    WITH count(*)                                                  AS total_documents,
        count(CASE WHEN doc.discrepancy_flag = true THEN 1 END)    AS flagged_documents
    RETURN
        total_documents,
        flagged_documents,
        CASE WHEN total_documents > 0
            THEN round(toFloat(flagged_documents) / total_documents * 100, 2)
            ELSE 0.0
END                                                                 AS overall_discrepancy_rate_pct
"""

_Q_ECONOMIC_VOLUME = """
    MATCH (inv:Document {doc_type: 'INVOICE'})
    RETURN
        count(inv)                                                  AS invoice_count,
        round(sum(toFloat(coalesce(inv.gross_amount,  0))), 2)      AS total_gross_eur,
        round(sum(toFloat(coalesce(inv.tax_amount,    0))), 2)      AS total_tax_eur,
        round(sum(toFloat(coalesce(inv.total_amount,  0))), 2)      AS total_net_eur
"""

_Q_DEGREE_SEQUENCE = """
    MATCH (c:Company)
    WITH COUNT { (c)-[:SUPPLIES]->() }                              AS out_degree
    RETURN collect(out_degree)                                      AS degrees
"""


class MacroMixin:
    """Estadísticas macroscópicas de la red B2B: estructura, rankings, series temporales y topología scale-free."""
    
    def get_macro_statistics(self) -> GraphMacroStats:
        """Crea una Snapshot completa del estado de la red en 8 consultas Neo4j.

        Las 5 consultas tabulares cubren la estructura del grafo y los rankings: conteo de nodos
        por etiqueta, aristas por tipo, top proveedores y compradores por grado de
        ``SUPPLIES``, y distribución de tipos de documento EDI.

        Las 3 consultas escalares calculan salud documental (total, flagged, tasa de discrepancia),
        volumen económico de facturas (bruto, neto, impuesto) y la secuencia de grados de salida. 
        Los indicadores scale-free (Gini, hubs) se derivan de esa secuencia en Python, no en Neo4j.

        Returns:
            ``GraphMacroStats`` con todos los indicadores macroscópicos de la red.
        """

        nodes_data     = self._fetch_data(_Q_NODES)
        edges_data     = self._fetch_data(_Q_EDGES)
        suppliers_data = self._fetch_data(_Q_TOP_SUPPLIERS)
        buyers_data    = self._fetch_data(_Q_TOP_BUYERS)
        doc_types_data = self._fetch_data(_Q_DOC_TYPES)

        doc_health  = self._fetch_data(_Q_DOCUMENT_HEALTH)[0]
        econ_volume = self._fetch_data(_Q_ECONOMIC_VOLUME)[0]
        degrees_row = self._fetch_data(_Q_DEGREE_SEQUENCE)[0]

        return GraphMacroStats(
            node_counts         = {str(r["label"]): int(r["total"]) for r in nodes_data if r.get("label")},
            relationship_counts = {str(r["relationship"]): int(r["total"]) for r in edges_data if r.get("relationship")},
            top_suppliers       = suppliers_data,
            top_buyers          = buyers_data,
            doc_type_counts     = {str(r["doc_type"]): int(r["total"]) for r in doc_types_data if r.get("doc_type")},
            economic_volume     = {
                "invoice_count":   econ_volume.get("invoice_count",   0),
                "total_gross_eur": econ_volume.get("total_gross_eur", 0.0),
                "total_tax_eur":   econ_volume.get("total_tax_eur",   0.0),
                "total_net_eur":   econ_volume.get("total_net_eur",   0.0),
            },
            document_health     = {
                "total_documents":              doc_health.get("total_documents",              0),
                "flagged_documents":            doc_health.get("flagged_documents",            0),
                "overall_discrepancy_rate_pct": doc_health.get("overall_discrepancy_rate_pct", 0.0),
            },
            scale_free_metrics  = self._build_scale_free_metrics(degrees_row.get("degrees", [])),
        )

    def get_temporal_distribution(self) -> pd.DataFrame:
        """Calcula la serie temporal mensual de actividad en la red B2B.
        
        Agrupa todos los documentos por mes via ``TimeBucket`` y calcula seis métricas por
        período mediante subqueries correlacionadas sobre el mismo conjunto de documentos.

        Returns:
            DataFrame con una fila por mes y las columnas:

                | Columna | Tipo | Descripción |
                |---|---|---|
                | ``year`` | int | Año |
                | ``month`` | int | Mes (1-12) |
                | ``documents`` | int | Total de documentos EDI emitidos |
                | ``flagged`` | int | Documentos con discrepancia |
                | ``total_gross_eur`` | float | Importe bruto agregado de facturas (€) |
                | ``active_companies`` | int | Empresas distintas que emitieron documentos |
                | ``active_products`` | int | Productos distintos referenciados |
                | ``active_connections`` | int | Pares proveedor→comprador activos |
        """
        return pd.DataFrame(self._fetch_data(_Q_TEMPORAL))

    # ── Helpers estáticos ─────────────────────────────────────────────────────

    @staticmethod
    def _gini_coefficient(values: list[int]) -> float:
        r"""Calcula el coeficiente de Gini para evaluar la desigualdad en la distribución de grados.

        Determina el nivel de concentración de enlaces en la red para evaluar si la 
        distribución de conexiones es homogénea o altamente desigual.

        Args:
            values: Secuencia con los grados de salida (*out-degree*) a evaluar.

        Returns:
            Coeficiente acotado en el rango [0.0, 1.0]. Se devuelve ``0.0`` si la lista está vacía
                o su sumatorio es cero.
        
        Note:
            Implementa la expresión discreta alternativa para el cálculo del coeficiente de Gini 
            en muestras ordenadas. (disponible en [Wikipedia](https://en.wikipedia.org/wiki/Gini_coefficient#Alternative_expressions)).

            $$G = \frac{2 \sum_{i=1}^{n} i \cdot v_i}{n \cdot \sum_{i=1}^{n} v_i} - \frac{n + 1}{n}$$

            La complejidad de $O(n \log n)$ se alcanza al ordenar el vector, lo que evita un 
            cálculo por parejas de coste cuadrático $O(n^2)$. Al ser la sumatoria posterior 
            puramente lineal $O(n)$, el coste asintótico total queda acotado exclusivamente 
            por la ordenación inicial.
            
            Finalmente, al unificar denominadores para optimizar la operación en un único paso, 
            la ecuación analítica completa que integra el cálculo de la sumatoria se define como:

            $$G = \frac{2 \sum_{i=1}^{n} (i \cdot v_i) - (n + 1) \cdot \text{total}}{n \cdot \text{total}}$$
            
            Ecuación que se implementa en el código de esta función.
            
        """
        if not values or sum(values) == 0:
            return 0.0
        sorted_vals  = sorted(values)
        n            = len(sorted_vals)
        total        = sum(sorted_vals)
        weighted_sum = sum((i + 1) * v for i, v in enumerate(sorted_vals))
        return round((2 * weighted_sum - (n + 1) * total) / (n * total), 4)

    @staticmethod
    def _build_scale_free_metrics(degrees: list[int]) -> dict[str, Any]:
        """Calcula los indicadores estadísticos que validan si la red LFR representa una topología scale-free.
        
        Args:
            degrees: Secuencia con el grado de salida por cada nodo ``Company``.

        Returns:
            Diccionario con los indicadores de topología:

                | Clave | Tipo | Descripción |
                |---|---|---|
                | ``mean_degree`` | float | Grado medio de salida |
                | ``median_degree`` | float | Mediana del grado de salida |
                | ``std_degree`` | float | Desviación estándar del grado |
                | ``max_degree`` | int | Grado máximo de salida |
                | ``min_degree`` | int | Grado mínimo de salida |
                | ``gini_coefficient`` | float | Coeficiente de desigualdad de Gini |
                | ``hub_count`` | int | Nº nodos clasificados como *hubs* |
                | ``hub_threshold`` | float | Umbral de corte empleado para los *hubs* |
                | ``max_mean_ratio`` | float | Factor de escala de la cola larga |
        
        Notes:
            Analiza la topología de la red mediante estadística descriptiva sobre 
            los grados de salida, validando dos propiedades clave de las 
            distribuciones de ley de potencias:
            
            * **Gini > 0.5**: Refleja la presencia de una desigualdad de conexiones 
                representativa de redes scale-free.
            * **max_mean_ratio >> 5**: Confirma la presencia de una cola derecha lo 
                bastante larga como para descartar una distribución aleatoria.
              
            Los *hubs* estructurales se clasifican siguiendo el umbral estadístico 
            determinado por una distancia superior a dos desviaciones estándar de la media.
        """
        if not degrees:
            return {}

        n        = len(degrees)
        mean_deg = sum(degrees) / n
        variance = sum((d - mean_deg) ** 2 for d in degrees) / n
        std_deg  = variance ** 0.5
        sorted_d = sorted(degrees)
        median_deg = (
            (sorted_d[n // 2 - 1] + sorted_d[n // 2]) / 2
            if n % 2 == 0
            else float(sorted_d[n // 2])
        )
        hub_threshold = mean_deg + 2 * std_deg

        return {
            "mean_degree":      round(mean_deg, 3),
            "median_degree":    round(median_deg, 3),
            "std_degree":       round(std_deg, 3),
            "max_degree":       sorted_d[-1],
            "min_degree":       sorted_d[0],
            "gini_coefficient": MacroMixin._gini_coefficient(degrees),
            "hub_count":        sum(1 for d in degrees if d > hub_threshold),
            "hub_threshold":    round(hub_threshold, 2),
            "max_mean_ratio":   round(sorted_d[-1] / mean_deg, 2) if mean_deg else 0,
        }
