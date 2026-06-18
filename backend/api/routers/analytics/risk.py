from __future__ import annotations

from fastapi import APIRouter

from backend.api.dependencies import read_json

router = APIRouter(prefix="/risk")


@router.get("")
def get_risk_concentration():
    return read_json("risk_concentration.json", default={})

@router.get("/commercial-impact")
def get_commercial_impact():
    return read_json("commercial_impact.json", default=[])

@router.get("/supplier-score")
def get_supplier_score():
    return read_json("supplier_risk_score.json", default=[])

@router.get("/buyer-fragility")
def get_buyer_fragility():
    return read_json("buyer_fragility.json", default=[])

@router.get("/overdue")
def get_overdue_exposure():
    return read_json("overdue_exposure.json", default=[])

@router.get("/contracts")
def get_contract_profile():
    return read_json("contract_profile.json", default={})

@router.get("/contracts-detail")
def get_contract_detail():
    return read_json("contract_detail.json", default=[])

@router.get("/geographic")
def get_geographic_risk():
    return read_json("geographic_risk.json", default=[])

@router.get("/synthesis/suppliers")
def get_cross_suppliers():
    return read_json("cross_suppliers.json", default=[])

@router.get("/synthesis/buyers")
def get_cross_buyers():
    return read_json("cross_buyers.json", default=[])