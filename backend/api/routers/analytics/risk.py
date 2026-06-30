from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from backend.api.dependencies import get_analyzer_instance, read_json
from backend.etl.analytics.analyzer import B2BGraphAnalyzer

router = APIRouter(prefix="/risk")


@router.get("")
def get_risk_concentration() -> dict:
    """Concentración de suministros en los proveedores con mayor 
    conectividad con aristas.

    Returns:
        Contenido de ``risk_concentration.json`` con el ``score`` agregado
            de los proveedores más críticos de la red.
    """
    return read_json("risk_concentration.json", default={})


@router.get("/commercial-impact")
def get_commercial_impact() -> list:
    """Impacto comercial potencial por caída de proveedores críticos.

    Returns:
        Registros de ``commercial_impact.json``.
    """
    return read_json("commercial_impact.json", default=[])


@router.get("/supplier-score")
def get_supplier_score() -> list:
    """Puntuación de riesgo compuesta por proveedor.

    Returns:
        Registros de ``supplier_risk_score.json`` con el score agregado.
    """
    return read_json("supplier_risk_score.json", default=[])


@router.get("/buyer-fragility")
def get_buyer_fragility() -> list:
    """Índice de fragilidad de compradores ante roturas de stock.

    Returns:
        Registros de ``buyer_fragility.json``.
    """
    return read_json("buyer_fragility.json", default=[])


@router.get("/overdue")
def get_overdue_exposure() -> list:
    """Exposición total en facturas vencidas sin pagar por proveedor.

    Returns:
        Registros de ``overdue_exposure.json``.
    """
    return read_json("overdue_exposure.json", default=[])


@router.get("/contracts")
def get_contract_profile() -> dict:
    """Distribución de tipos de contrato en la red B2B.

    Returns:
        Contenido de ``contract_profile.json``.
    """
    return read_json("contract_profile.json", default={})


@router.get("/contracts-detail")
def get_contract_detail() -> list:
    """Detalles de contratos por cada par proveedor-comprador.

    Returns:
        Registros de ``contract_detail.json``.
    """
    return read_json("contract_detail.json", default=[])


@router.get("/geographic")
def get_geographic_risk() -> list:
    """Concentración de proveedores con discrepancias por región.

    Returns:
        Registros de ``geographic_risk.json``.
    """
    return read_json("geographic_risk.json", default=[])


@router.get("/synthesis/suppliers")
def get_cross_suppliers() -> list:
    """Síntesis cruzada de riesgo para proveedores clave.

    Returns:
        Registros de ``cross_suppliers.json``.
    """
    return read_json("cross_suppliers.json", default=[])


@router.get("/synthesis/buyers")
def get_cross_buyers() -> list:
    """Síntesis cruzada de riesgo para compradores clave.

    Returns:
        Registros de ``cross_buyers.json``.
    """
    return read_json("cross_buyers.json", default=[])


# ── Endpoints en tiempo real ──────────────────────────────────────────────────
@router.get("/buyer-supplier-recommendations")
def get_buyer_supplier_recommendations(
    buyer: str = Query(..., description="Razón social exacta del comprador"),
    analyzer: B2BGraphAnalyzer = Depends(get_analyzer_instance),
) -> list[dict]:
    """Proveedores recomendados para un comprador dado.

    Consulta en tiempo real el grafo Neo4j para calcular proveedores
    candidatos que minimicen la dependencia del comprador.

    Args:
        buyer: Razón social exacta del comprador (``legal_name`` en Neo4j).
        analyzer: Instancia del analizador con conexión activa a Neo4j.

    Returns:
        Proveedores recomendados con su puntuación, o ``[]`` si
            no se encuentran candidatos.
    """
    df = analyzer.get_buyer_supplier_recommendations(buyer)
    return df.to_dict(orient="records") if not df.empty else []


@router.get("/supplier-contracts")
def get_supplier_contracts(
    supplier: str = Query(..., description="Razón social exacta del proveedor"),
    analyzer: B2BGraphAnalyzer = Depends(get_analyzer_instance),
) -> list[dict]:
    """Detalles de contratos activos de un proveedor específico.

    Args:
        supplier: Razón social exacta del proveedor (``legal_name`` en Neo4j).
        analyzer: Instancia del analizador con conexión activa a Neo4j.

    Returns:
        Contratos del proveedor, o ``[]`` si no hay datos.
    """
    df = analyzer.get_supplier_contracts(supplier)
    return df.to_dict(orient="records") if not df.empty else []


@router.get("/supplier-pair-overdue")
def get_supplier_pair_overdue(
    supplier: str = Query(..., description="Razón social exacta del proveedor"),
    buyer: str = Query(..., description="Razón social exacta del comprador"),
    analyzer: B2BGraphAnalyzer = Depends(get_analyzer_instance),
) -> list[dict]:
    """Facturas vencidas entre un par proveedor-comprador concreto.

    Args:
        supplier: Razón social exacta del proveedor.
        buyer: Razón social exacta del comprador.
        analyzer: Instancia del analizador con conexión activa a Neo4j.

    Returns:
        Facturas vencidas del par, o ``[]`` si no hay datos.
    """
    df = analyzer.get_supplier_pair_overdue_invoices(supplier, buyer)
    return df.to_dict(orient="records") if not df.empty else []


@router.get("/supplier-invoices")
def get_supplier_invoices(
    supplier: str = Query(..., description="Razón social exacta del proveedor"),
    analyzer: B2BGraphAnalyzer = Depends(get_analyzer_instance),
) -> list[dict]:
    """Todas las facturas emitidas por un proveedor específico.

    Args:
        supplier: Razón social exacta del proveedor.
        analyzer: Instancia del analizador con conexión activa a Neo4j.

    Returns:
        Facturas del proveedor, o ``[]`` si no hay datos.
    """
    df = analyzer.get_supplier_invoices(supplier)
    return df.to_dict(orient="records") if not df.empty else []