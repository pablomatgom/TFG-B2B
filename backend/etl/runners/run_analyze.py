from __future__ import annotations

import logging
from dataclasses import asdict
from datetime import datetime, UTC
from pathlib import Path
from typing import Optional

from backend.core.config import Settings
from backend.core.utils import write_step_artifact, export_dict_to_json, export_df_to_json
from backend.etl.analytics.analyzer import B2BGraphAnalyzer

logger = logging.getLogger(__name__)


def _safe_df(label: str, fn, export_dir: Path, filename: str) -> Optional[Path]:
    """Run an analytics method and export it; log and continue on failure."""
    try:
        return export_df_to_json(fn(), export_dir, filename)
    except Exception as exc:
        logger.error("[FASE 3] %s falló — %s: %s", label, type(exc).__name__, exc)
        return None


def _safe_dict(label: str, fn, export_dir: Path, filename: str) -> Optional[Path]:
    """Same as _safe_df but for dict-returning methods."""
    try:
        return export_dict_to_json(fn(), export_dir, filename)
    except Exception as exc:
        logger.error("[FASE 3] %s falló — %s: %s", label, type(exc).__name__, exc)
        return None


def run_analyze(settings: Settings) -> Path:
    """
    Fase 3: Análisis de la topología de red y exportación de resultados a JSON.
    Cada exportación es independiente: un fallo en una no cancela las demás.
    """
    export_dir = settings.data_export_dir
    export_dir.mkdir(parents=True, exist_ok=True)

    logger.info("")
    logger.info("[FASE 3] Analítica Avanzada y Exportación iniciada.")
    logger.info("         Directorio destino: '%s/'", export_dir.name)

    with B2BGraphAnalyzer(
        neo4j_uri=settings.neo4j_uri,
        neo4j_user=settings.neo4j_user,
        neo4j_password=settings.neo4j_password,
        neo4j_database=settings.neo4j_database,
    ) as analyzer:
        analyzer.verify_connection()

        # ── Macro & temporal ────────────────────────────────────────────────
        macro_path = _safe_dict(
            "get_macro_statistics",
            lambda: asdict(analyzer.get_macro_statistics()),
            export_dir, "macro_statistics.json",
        )
        temporal_path = _safe_df(
            "get_temporal_distribution",
            analyzer.get_temporal_distribution,
            export_dir, "temporal_series.json",
        )

        # ── Lineage ─────────────────────────────────────────────────────────
        backward_path = _safe_df(
            "get_backward_traceability",
            analyzer.get_backward_traceability,
            export_dir, "backward_traceability.json",
        )
        exact_paths_path = _safe_df(
            "extract_lineage_paths",
            analyzer.extract_lineage_paths,
            export_dir, "lineage_exact_paths.json",
        )
        forward_path = _safe_df(
            "get_forward_traceability",
            analyzer.get_forward_traceability,
            export_dir, "forward_traceability.json",
        )

        # ── Risk & operational ───────────────────────────────────────────────
        # commercial_impact_path = _safe_df(
        #     "compute_commercial_impact",
        #     lambda: analyzer.compute_commercial_impact(limit=100),
        #     export_dir, "commercial_impact.json",
        # )
        # risk_path = _safe_dict(
        #     "get_supplier_risk_concentration",
        #     lambda: analyzer.get_supplier_risk_concentration(top_n=10),
        #     export_dir, "risk_concentration.json",
        # )
        # discrepancy_sup_path = _safe_df(
        #     "get_discrepancy_rate_by_supplier",
        #     analyzer.get_discrepancy_rate_by_supplier,
        #     export_dir, "discrepancy_by_supplier.json",
        # )
        # lead_time_path = _safe_df(
        #     "get_lead_time_compliance",
        #     analyzer.get_lead_time_compliance,
        #     export_dir, "lead_time_compliance.json",
        # )
        # payment_path = _safe_df(
        #     "get_payment_terms_exposure",
        #     analyzer.get_payment_terms_exposure,
        #     export_dir, "payment_exposure.json",
        # )

        # ── GDS (commented out until enabled) ───────────────────────────────
        # bottlenecks_path = _safe_df(
        #     "compute_betweenness_centrality",
        #     analyzer.compute_betweenness_centrality,
        #     export_dir, "bottlenecks.json",
        # )
        # communities_path = _safe_df(
        #     "detect_communities_louvain",
        #     analyzer.detect_communities_louvain,
        #     export_dir, "communities.json",
        # )

    exported = [
        p.name for p in [
            # macro_path, temporal_path,
            backward_path, exact_paths_path, forward_path,
            # risk_path, discrepancy_sup_path, lead_time_path, payment_path,
        ]
        if p is not None
    ]
    failed = 10 - len(exported)

    logger.info("[FASE 3] Completada. %d/%d archivos exportados.", len(exported), 10)
    if failed:
        logger.warning("[FASE 3] %d exportación(es) fallaron — revisa los logs anteriores.", failed)

    payload = {
        "step":           "analyze",
        "status":         "ok" if not failed else "partial",
        "timestamp_utc":  datetime.now(UTC).isoformat(),
        "exported_files": exported,
        "failed_exports": failed,
        "message":        f"Fase analítica completada. {len(exported)}/10 archivos en '{export_dir.name}/'.",
    }
    return write_step_artifact(settings.data_processed_dir, "analyze", payload)