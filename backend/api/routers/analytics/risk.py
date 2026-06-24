from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from backend.api.dependencies import get_analyzer_instance, read_json
from backend.etl.analytics.analyzer import B2BGraphAnalyzer

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

@router.get("/buyer-supplier-recommendations")
def get_buyer_supplier_recommendations(
    buyer: str = Query(..., description="Razón social exacta del comprador"),
    analyzer: B2BGraphAnalyzer = Depends(get_analyzer_instance),
):
    df = analyzer.get_buyer_supplier_recommendations(buyer)
    return df.to_dict(orient="records") if not df.empty else []

@router.get("/supplier-contracts")
def get_supplier_contracts(
    supplier: str = Query(..., description="Razón social exacta del proveedor"),
    analyzer: B2BGraphAnalyzer = Depends(get_analyzer_instance),
):
    df = analyzer.get_supplier_contracts(supplier)
    return df.to_dict(orient="records") if not df.empty else []

@router.get("/supplier-pair-overdue")
def get_supplier_pair_overdue(
    supplier: str = Query(..., description="Razón social exacta del proveedor"),
    buyer: str = Query(..., description="Razón social exacta del comprador"),
    analyzer: B2BGraphAnalyzer = Depends(get_analyzer_instance),
):
    df = analyzer.get_supplier_pair_overdue_invoices(supplier, buyer)
    return df.to_dict(orient="records") if not df.empty else []

@router.get("/supplier-invoices")
def get_supplier_invoices(
    supplier: str = Query(..., description="Razón social exacta del proveedor"),
    analyzer: B2BGraphAnalyzer = Depends(get_analyzer_instance),
):
    df = analyzer.get_supplier_invoices(supplier)
    return df.to_dict(orient="records") if not df.empty else []