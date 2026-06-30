from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from backend.etl.analytics.analyzer import B2BGraphAnalyzer
from backend.api.dependencies import get_analyzer_instance

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/")
def root() -> dict:
    """Ping básico que confirma que el servidor FastAPI está en pie.

    Returns:
        ``{"status": "Online", "database": "Neo4j Backend Ready"}``
    """
    return {"status": "Online", "database": "Neo4j Backend Ready"}


@router.get("/api/health")
def api_health_check(analyzer: B2BGraphAnalyzer = Depends(get_analyzer_instance)) -> dict:
    """Comprueba la conectividad en tiempo real con Neo4j.

    Ejecuta una consulta contra el grafo para verificar que el driver puede
    abrir sesiones y recibir respuestas.

    Returns:
        ``{"status": "ok", "message": "..."}`` si la conexión es estable.

    Raises:
        HTTPException: 503 si Neo4j no responde o el driver no puede conectar.
    """
    try:
        analyzer.verify_connection()
        return {"status": "ok", "message": "Conexión estable con Neo4j"}
    except Exception as e:
        logger.error("Fallo en Health Check: %s", e)
        raise HTTPException(status_code=503, detail="Neo4j offline o inaccesible.")
