"""Orquestador End-to-End del pipeline completo (Fases 1 → 2 → 3 → Seed).

Encadena los cuatro runners en orden lógico estricto y agrega un artefacto
de resumen con la lista de pasos ejecutados y sus rutas de auditoría.
"""
from __future__ import annotations

import logging
from datetime import datetime, UTC
from pathlib import Path

from backend.core.config import Settings
from backend.core.utils import write_step_artifact
from backend.etl.runners.run_generate import run_generate
from backend.etl.runners.run_load import run_load
from backend.etl.runners.run_analyze import run_analyze
from backend.etl.runners.run_seed import run_seed


def run_all(
    settings: Settings,
    rows: int,
    avg_degree_products: int,
    avg_degree_rel_supplies: int,
    avg_degree_documents: int,
    gamma: float,
    beta: float,
    mu: float,
    batch_size_loader: int,
    clear_db: bool = False,
    skip_seed: bool = False,
) -> list[Path]:
    """Ejecuta el pipeline completo de principio a fin.

    Encadena las cuatro fases en orden estricto: generación de CSVs,
    carga en Neo4j, análisis del grafo y seed de usuarios demo. El paso
    ``seed`` puede omitirse con ``skip_seed=True``.

    Args:
        settings: Configuración del sistema (rutas, semilla, conexión Neo4j).
        rows: Número de empresas a generar.
        avg_degree_products: Grado de salida medio de productos por proveedor.
        avg_degree_rel_supplies: Grado de salida medio en la red de suministros.
        avg_degree_documents: Número medio de documentos por par
            proveedor-comprador.
        gamma: Exponente LFR de la distribución de grado.
        beta: Exponente LFR de la distribución de tamaños de comunidad.
        mu: Coeficiente de mezcla LFR (fracción de aristas inter-comunidad).
        batch_size_loader: Filas por lote para la ingesta en Neo4j.
        clear_db: Si es ``True``, vacía el grafo antes de cargar.
        skip_seed: Si es ``True``, omite el paso de seed de usuarios demo.

    Returns:
        Rutas a los artefactos JSON de auditoría de cada paso,
            incluyendo el resumen final ``all_last_run.json``.
    """
    logging.info(f"--- INICIO ORQUESTACIÓN END-TO-END (Seed: {settings.seed}) ---")

    steps_run = ["generate", "load", "analyze"]

    artifacts = [
        run_generate(
            settings, csv_target="all",
            rows=rows, avg_degree_products=avg_degree_products,
            avg_degree_rel_supplies=avg_degree_rel_supplies,
            avg_degree_documents=avg_degree_documents,
            gamma=gamma, beta=beta, mu=mu,
        ),
        run_load(settings, batch_size_loader=batch_size_loader, clear_db=clear_db),
        run_analyze(settings),
    ]

    if not skip_seed:
        artifacts.append(run_seed(settings))
        steps_run.append("seed")

    summary = {
        "step": "all",
        "status": "ok",
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "executed_steps": steps_run,
        "artifacts": [str(p) for p in artifacts],
    }
    artifacts.append(write_step_artifact(settings.data_processed_dir, "all", summary))
    return artifacts