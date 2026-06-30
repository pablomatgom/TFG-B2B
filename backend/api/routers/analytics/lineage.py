from __future__ import annotations

from fastapi import APIRouter

from backend.api.dependencies import read_json

router = APIRouter(prefix="/lineage")



@router.get("/backward")
def get_backward_lineage() -> list:
    """Trazabilidad hacia atrás: factura → pedido origen.

    Returns:
        Registros de ``backward_traceability.json``, ordenados por
            riesgo financiero descendente.
    """
    return read_json("backward_traceability.json", default=[])


@router.get("/exact-paths")
def get_lineage_exact_paths() -> list:
    """Rutas exactas de la cadena de documento a documento en el grafo.

    Returns:
        Registros de ``lineage_exact_paths.json`` con las cadenas
            completas ``FULFILLS`` reconstruidas.
    """
    return read_json("lineage_exact_paths.json", default=[])


@router.get("/forward")
def get_forward_traceability() -> list:
    """Trazabilidad hacia adelante: pedido → documentos derivados.

    Returns:
        Registros de ``forward_traceability.json``.
    """
    return read_json("forward_traceability.json", default=[])