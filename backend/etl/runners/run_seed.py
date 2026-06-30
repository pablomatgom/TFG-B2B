"""Orquestador del paso de seeding: crea usuarios demo en SQLite desde Neo4j.

Se ejecuta automáticamente al final de :func:`~backend.etl.runners.run_all.run_all`
(a menos que se pase ``skip_seed=True``).
"""
from __future__ import annotations

import logging
from datetime import datetime, UTC
from pathlib import Path

from backend.core.config import Settings
from backend.core.utils import write_step_artifact
from backend.auth.db.seed_users import seed

logger = logging.getLogger(__name__)


def run_seed(settings: Settings) -> Path:
    """Crea usuarios demo en SQLite desde los nodos Company existentes en Neo4j.
    
    Por cada nodo de tipo empresa en el grafo, inicializa automáticamente 
    un usuario con credenciales por defecto. Esto permite sincronizar el 
    sistema de autenticación con los datos sintéticos cargados en la BD.

    Args:
        settings: Configuración del sistema (rutas, conexión Neo4j).

    Returns:
        Ruta al artefacto JSON de auditoría escrito en
            ``data/processed/seed_last_run.json``.
    """
    logger.info("--- INICIO SEED DE USUARIOS DEMO ---")

    stats = seed(settings)

    summary = {
        "step": "seed",
        "status": "ok",
        "timestamp_utc": datetime.now(UTC).isoformat(),
        **stats,
    }
    artifact = write_step_artifact(settings.data_processed_dir, "seed", summary)
    logger.info(f"--- FIN SEED -> {artifact} ---")
    return artifact