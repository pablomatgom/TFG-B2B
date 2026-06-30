from __future__ import annotations

from fastapi import APIRouter

from backend.api.dependencies import read_json

router = APIRouter(prefix="/lead-time")


@router.get("")
def get_lead_time_compliance() -> list:
    """Cumplimiento de plazos de entrega por categoría de producto.

    Returns:
        Registros de ``lead_time_compliance.json`` con demora media
            vs. baseline y porcentaje de entregas tardías por categoría.
    """
    return read_json("lead_time_compliance.json", default=[])