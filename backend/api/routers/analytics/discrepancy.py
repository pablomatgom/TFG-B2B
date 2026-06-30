from __future__ import annotations

from fastapi import APIRouter

from backend.api.dependencies import read_json

router = APIRouter(prefix="/discrepancy-suppliers")


@router.get("")
def get_discrepancy_by_supplier() -> list:
    """Devuelve los proveedores con mayor tasa de discrepancias en facturas.

    Returns:
        Registros de ``discrepancy_by_supplier.json``, ordenados por
            tasa de discrepancia descendente (mín. 5 facturas emitidas).
    """
    return read_json("discrepancy_by_supplier.json", default=[])