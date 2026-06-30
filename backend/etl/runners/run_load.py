"""Orquestador de la Fase 2: ingesta masiva de CSVs sintéticos en Neo4j.

Crea una instancia de :class:`~backend.etl.loader.Neo4jBulkLoader`,
verifica la conectividad, aplica constraints e índices y carga los cinco
datasets en el orden garantizado por el loader.
"""
from __future__ import annotations
from datetime import datetime, UTC
import logging
from pathlib import Path

from backend.core.config import Settings
from backend.core.utils import write_step_artifact
from backend.etl.loader import Neo4jBulkLoader

def run_load(settings: Settings, batch_size_loader: int, clear_db: bool = False) -> Path:
    """Ejecuta la Fase 2 del pipeline: carga los CSVs sintéticos en Neo4j.

    Utiliza ``Neo4jBulkLoader`` de forma segura para gestionar la carga masiva, 
    asegurando el cierre automático de la conexión. Si se activa ``clear_db``, 
    purga la base de datos por completo antes de empezar.

    Args:
        settings: Configuración del sistema (rutas, conexión Neo4j).
        batch_size_loader: Número de filas por lote Neo4j.
        clear_db: Si es ``True``, elimina todos los nodos y relaciones antes
            de iniciar la carga.

    Returns:
        Ruta al artefacto JSON de auditoría escrito en
            ``data/processed/load_last_run.json``.
    """
    logging.info("")
    logging.info("[FASE 2] Ingesta Masiva en Neo4j iniciada.")
    logging.info(f"         Target DB: '{settings.neo4j_database}' | Purga previa: {'Activada' if clear_db else 'Desactivada'}")
    logging.info(f"         Batch Size: {batch_size_loader} registros/lote")
    
    with Neo4jBulkLoader(
        neo4j_uri=settings.neo4j_uri,
        neo4j_user=settings.neo4j_user,
        neo4j_password=settings.neo4j_password,
        neo4j_database=settings.neo4j_database,
        batch_size=batch_size_loader,
    ) as loader:
        loader.verify_connection()
        
        if clear_db:
            loader.clear_database()
            
        loader.create_constraints_and_indexes()
        load_stats = loader.load_from_directory(settings.data_synthetic_dir)
        
    payload = {
        "step": "load",
        "status": "ok",
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "batch_size": batch_size_loader,
        "cleared_db": clear_db,
        "neo4j_uri": settings.neo4j_uri,
        "neo4j_database": settings.neo4j_database,
        "message": f"Fase de carga completada. Nodos y relaciones ingestados: {load_stats['total_rows']}",
        "stats": load_stats 
    }
    return write_step_artifact(settings.data_processed_dir, "load", payload)
