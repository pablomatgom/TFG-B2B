from __future__ import annotations

from fastapi import APIRouter

from backend.api.dependencies import read_json

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/macro")
def get_macro_dashboard() -> dict:
    """Devuelve estadísticas macro y la serie temporal de documentos.

    Envia los datos pre-computados por el pipeline de análisis. Actualiza
    automáticamente en el próximo ``analyze`` sin reiniciar la API.

    Returns:
        Claves ``macro_stats`` (``macro_statistics.json``) y
            ``temporal_series`` (``temporal_series.json``).
    """
    return {
        "macro_stats":     read_json("macro_statistics.json", default={}),
        "temporal_series": read_json("temporal_series.json",  default=[]),
    }