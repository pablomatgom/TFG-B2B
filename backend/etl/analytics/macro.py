from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


# ══════════════════════════════════════════════════════════════════════════════
# DATA CLASS
# ══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class GraphMacroStats:
    """Snapshot inmutable de las métricas macroscópicas de la red B2B."""

    # ── Estructura del grafo ──────────────────────────────────────────────────
    node_counts:           dict[str, int]        # nodos por etiqueta
    relationship_counts:   dict[str, int]        # aristas por tipo

    # ── Rankings ─────────────────────────────────────────────────────────────
    top_suppliers:         list[dict[str, Any]]  # top-50 por grado de salida SUPPLIES
    top_buyers:            list[dict[str, Any]]  # top-50 por grado de entrada SUPPLIES
    doc_type_counts:       dict[str, int]        # distribución de tipos EDI

    # ── Finanzas ─────────────────────────────────────────────────────────────
    economic_volume:       dict[str, Any]        # volumen bruto / neto / impuesto de facturas

    # ── Calidad documental ────────────────────────────────────────────────────
    document_health:       dict[str, Any]        # total docs, flagged, tasa de discrepancia

    # ── Topología Scale-Free ──────────────────────────────────────────────────
    scale_free_metrics:    dict[str, Any]        # Gini, hubs, distribución de grado


# ══════════════════════════════════════════════════════════════════════════════
# CYPHER QUERIES
# ══════════════════════════════════════════════════════════════════════════════

# ─── Network structure ────────────────────────────────────────────────────────

_Q_NODES = (
    "MATCH (n) RETURN labels(n)[0] AS label, count(n) AS total ORDER BY label"
)

_Q_EDGES = (
    "MATCH ()-[r]->() RETURN type(r) AS relationship, count(r) AS total ORDER BY relationship"
)

# ─── Rankings ─────────────────────────────────────────────────────────────────
    # LIMIT 50
_Q_TOP_SUPPLIERS = """
    MATCH (supplier:Company)-[r:SUPPLIES]->(buyer:Company)
    RETURN supplier.company_id AS company_id,
           supplier.legal_name AS legal_name,
           count(r)            AS supplies_out,
           avg(r.agreed_volume_baseline) AS avg_agreed_volume
    ORDER BY supplies_out DESC, avg_agreed_volume DESC
"""
    # LIMIT 50  mirar si dejar o ponerlo
_Q_TOP_BUYERS = """
    MATCH (supplier:Company)-[r:SUPPLIES]->(buyer:Company)
    RETURN buyer.company_id AS company_id,
           buyer.legal_name AS legal_name,
           count(r)         AS supplies_in,
           avg(r.agreed_volume_baseline) AS avg_agreed_volume
    ORDER BY supplies_in DESC, avg_agreed_volume DESC
"""

_Q_DOC_TYPES = (
    "MATCH (d:Document) RETURN d.doc_type AS doc_type, count(d) AS total ORDER BY total DESC"
)

# ─── Temporal series ──────────────────────────────────────────────────────────
# Three metrics per month:
#   documents      — all EDI documents issued that month
#   flagged        — subset with discrepancy_flag = true
#   total_gross_eur — aggregated invoice gross amount (INVOICE doc_type only)

_Q_TEMPORAL = """
    MATCH (d:Document)-[:Issue_on]->(tb:TimeBucket)
    RETURN
        tb.year  AS year,
        tb.month AS month,
        count(d) AS documents,
        count(CASE WHEN d.discrepancy_flag = true THEN 1 END) AS flagged,
        round(
            sum(CASE WHEN d.doc_type = 'INVOICE'
                     THEN toFloat(coalesce(d.gross_amount, 0))
                     ELSE 0 END),
            2
        ) AS total_gross_eur
    ORDER BY year, month
"""

# ─── Geographic distribution ──────────────────────────────────────────────────

_Q_GEOGRAPHY = """
    MATCH (c:Company)
    WHERE c.latitude IS NOT NULL AND c.longitude IS NOT NULL
    RETURN c.city                        AS name,
           [c.longitude, c.latitude]     AS coordinates,
           count(c)                      AS weight
    ORDER BY weight DESC
"""

# ─── Consolidated scalars — 1 round-trip ──────────────────────────────────────
# Combines three independent sub-queries into one database call:
#   CALL 1 → document health  (total docs, flagged count, discrepancy rate)
#   CALL 2 → economic volume  (invoice count + gross/tax/net sums)
#   CALL 3 → degree sequence  (out-degree per Company node using Neo4j 5 COUNT{})

_Q_GLOBAL_SCALARS = """
    CALL {
        MATCH (doc:Document)
        RETURN
            count(*)                                                 AS total_docs,
            count(CASE WHEN doc.discrepancy_flag = true THEN 1 END)  AS flagged_docs
    }
    CALL {
        MATCH (inv:Document {doc_type: 'INVOICE'})
        RETURN
            count(inv)                                               AS invoice_count,
            round(sum(toFloat(coalesce(inv.gross_amount,  0))), 2)   AS total_gross_eur,
            round(sum(toFloat(coalesce(inv.tax_amount,    0))), 2)   AS total_tax_eur,
            round(sum(toFloat(coalesce(inv.total_amount,  0))), 2)   AS total_net_eur
    }
    CALL {
        MATCH (c:Company)
        WITH COUNT { (c)-[:SUPPLIES]->() } AS out_degree
        RETURN collect(out_degree) AS degrees
    }
    RETURN
        total_docs   AS total_documents,
        flagged_docs AS flagged_documents,
        CASE WHEN total_docs > 0
             THEN round(toFloat(flagged_docs) / total_docs * 100, 2)
             ELSE 0.0
        END          AS overall_discrepancy_rate_pct,
        invoice_count,
        total_gross_eur,
        total_tax_eur,
        total_net_eur,
        degrees
"""


# ══════════════════════════════════════════════════════════════════════════════
# PURE HELPER FUNCTIONS  (stateless, no side effects)
# ══════════════════════════════════════════════════════════════════════════════

def _gini_coefficient(values: list[int]) -> float:
    """
    Gini coefficient of a degree sequence (0 = perfect equality, 1 = maximum inequality).
    A value >0.5 on SUPPLIES out-degrees is the canonical fingerprint of a scale-free network.
    """
    if not values or sum(values) == 0:
        return 0.0
    sorted_vals  = sorted(values)
    n            = len(sorted_vals)
    total        = sum(sorted_vals)
    weighted_sum = sum((i + 1) * v for i, v in enumerate(sorted_vals))
    return round((2 * weighted_sum - (n + 1) * total) / (n * total), 4)


def _build_scale_free_metrics(degrees: list[int]) -> dict[str, Any]:
    """
    Validates whether the LFR-generated network exhibits scale-free (power-law) topology.

    Returned indicators:
      gini_coefficient  — degree inequality (>0.5 → scale-free)
      max_mean_ratio    — max_degree / mean_degree (>>5 → fat-tailed distribution)
      hub_count         — nodes with out-degree > μ + 2σ  (structural chokepoints)
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
        "node_count":       n,
        "mean_degree":      round(mean_deg, 3),
        "median_degree":    round(median_deg, 3),
        "std_degree":       round(std_deg, 3),
        "max_degree":       max(degrees),
        "min_degree":       min(degrees),
        "gini_coefficient": _gini_coefficient(degrees),
        "hub_count":        sum(1 for d in degrees if d > hub_threshold),
        "hub_threshold":    round(hub_threshold, 2),
        "max_mean_ratio":   round(max(degrees) / mean_deg, 2) if mean_deg else 0,
    }


# ══════════════════════════════════════════════════════════════════════════════
# MIXIN
# ══════════════════════════════════════════════════════════════════════════════

class MacroMixin:
    """Estadísticas macroscópicas de la red y distribución geográfica."""

    # ── Public API ────────────────────────────────────────────────────────────

    def get_macro_statistics(self) -> GraphMacroStats:
        """
        Full network health snapshot in 6 queries:
          5 tabular → node/edge counts, rankings, doc-type distribution
          1 scalar  → document health + economic volume + degree sequence (one round-trip)
        """
        # Tabular queries — each returns multiple rows
        nodes_data     = self._fetch_data(_Q_NODES)
        edges_data     = self._fetch_data(_Q_EDGES)
        suppliers_data = self._fetch_data(_Q_TOP_SUPPLIERS)
        buyers_data    = self._fetch_data(_Q_TOP_BUYERS)
        doc_types_data = self._fetch_data(_Q_DOC_TYPES)

        # Scalar query — always returns exactly 1 row
        scalars = self._fetch_data(_Q_GLOBAL_SCALARS)[0]

        economic_volume: dict[str, Any] = {
            "invoice_count":   scalars.get("invoice_count",   0),
            "total_gross_eur": scalars.get("total_gross_eur", 0.0),
            "total_tax_eur":   scalars.get("total_tax_eur",   0.0),
            "total_net_eur":   scalars.get("total_net_eur",   0.0),
        }

        document_health: dict[str, Any] = {
            "total_documents":              scalars.get("total_documents",              0),
            "flagged_documents":            scalars.get("flagged_documents",            0),
            "overall_discrepancy_rate_pct": scalars.get("overall_discrepancy_rate_pct", 0.0),
        }

        return GraphMacroStats(
            node_counts         = {str(r["label"]): int(r["total"]) for r in nodes_data if r.get("label")},
            relationship_counts = {str(r["relationship"]): int(r["total"]) for r in edges_data if r.get("relationship")},
            top_suppliers       = suppliers_data,
            top_buyers          = buyers_data,
            doc_type_counts     = {str(r["doc_type"]): int(r["total"]) for r in doc_types_data if r.get("doc_type")},
            economic_volume     = economic_volume,
            document_health     = document_health,
            scale_free_metrics  = _build_scale_free_metrics(scalars.get("degrees", [])),
        )

    def get_network_geography(self) -> list[dict[str, Any]]:
        """City coordinates with company-count weight — live query used by the Spain map."""
        return self._fetch_data(_Q_GEOGRAPHY)

    def get_temporal_distribution(self) -> pd.DataFrame:
        """Monthly time series: document count, flagged count, and invoice gross amount per month."""
        return pd.DataFrame(self._fetch_data(_Q_TEMPORAL))
