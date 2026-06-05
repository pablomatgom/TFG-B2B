from __future__ import annotations

from fastapi import APIRouter

from backend.api.dependencies import read_json

router = APIRouter(prefix="/lead-time")


@router.get("")
def get_lead_time_compliance():
    return read_json("lead_time_compliance.json", default=[])