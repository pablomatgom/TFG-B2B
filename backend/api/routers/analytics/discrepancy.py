from __future__ import annotations

from fastapi import APIRouter

from backend.api.dependencies import read_json

router = APIRouter(prefix="/discrepancy-suppliers")


@router.get("")
def get_discrepancy_by_supplier():
    return read_json("discrepancy_by_supplier.json", default=[])