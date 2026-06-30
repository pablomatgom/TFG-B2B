from __future__ import annotations

from fastapi import APIRouter

from backend.api.dependencies import read_json

router = APIRouter(prefix="/payment")


@router.get("")
def get_payment_exposure() -> list:
    """Devuelve los proveedores con mayor exposición total en facturas pendientes.

    Returns:
        Registros de ``payment_exposure.json`` ordenados por importe
            total pendiente descendente.
    """
    return read_json("payment_exposure.json", default=[])