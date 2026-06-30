from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from backend.etl.analytics.analyzer import B2BGraphAnalyzer
from backend.auth.db.database import User
from backend.api.dependencies import get_analyzer_instance, get_current_user, neo4j_to_dict
from backend.api.models.company import CompanyProfileUpdate, DocumentStatusUpdate

from backend.core.config import load_settings 

logger = logging.getLogger(__name__)

router = APIRouter(tags=["company"])

settings = load_settings()


@router.get("/api/company/me")
def get_my_company(
    current_user: User = Depends(get_current_user),
    analyzer: B2BGraphAnalyzer = Depends(get_analyzer_instance),
) -> dict:
    """Devuelve el nodo ``Company`` en Neo4j asociado al usuario autenticado.

    Args:
        current_user: Usuario resuelto por ``Depends(get_current_user)`` a partir del JWT.
        analyzer: Sesión ``B2BGraphAnalyzer`` inyectada por ``Depends(get_analyzer_instance)``.

    Returns:
        Todas las propiedades del nodo ``Company`` devueltos desde Neo4j.

    Raises:
        HTTPException: 401 si el token es inválido.
        HTTPException: 404 si no existe un nodo ``Company`` con el ``company_id`` del usuario.
    """
    with analyzer._driver.session(database=settings.neo4j_database) as session:
        rec = session.run(
            "MATCH (c:Company {company_id: $cid}) RETURN c",
            cid=current_user.company_id,
        ).single()
    if not rec:
        raise HTTPException(status_code=404, detail="Empresa no encontrada en Neo4j")
    return neo4j_to_dict(rec["c"])


@router.patch("/api/company/me")
def update_my_company(
    body: CompanyProfileUpdate,
    current_user: User = Depends(get_current_user),
    analyzer: B2BGraphAnalyzer = Depends(get_analyzer_instance),
) -> dict:
    """Actualiza parcialmente el perfil de la empresa del usuario autenticado.

    Solo los campos opcionales de ``body`` se modifican en Neo4j. 
    Los campos no incluidos en la petición permanecen sin cambios.

    Args:
        body: Campos a actualizar (todos opcionales).
        current_user: Usuario autenticado que realiza la petición.
        analyzer: Instancia del analizador con conexión activa a Neo4j.

    Returns:
        ``{"document_id": ..., "status": ...}`` con el valor actualizado.

    Raises:
        HTTPException: 400 si el body no contiene ningún campo a actualizar.
        HTTPException: 404 si el nodo ``Company`` no existe en Neo4j.
    
    Note:
        Sin conexión al frontend. Previsto para desarrollos futuros.
    """
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No hay campos a actualizar")
    set_clause = ", ".join(f"c.{k} = ${k}" for k in updates)
    query = f"MATCH (c:Company {{company_id: $cid}}) SET {set_clause} RETURN c"
    with analyzer._driver.session(database=analyzer._database) as session:
        rec = session.run(query, cid=current_user.company_id, **updates).single()
    if not rec:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    return neo4j_to_dict(rec["c"])


@router.get("/api/company/documents")
def get_my_documents(
    current_user: User = Depends(get_current_user),
    analyzer: B2BGraphAnalyzer = Depends(get_analyzer_instance),
) -> list[dict]:
    """Lista los últimos 200 documentos EDI emitidos por la empresa del usuario.

    Ejecuta una consulta Cypher en tiempo real y serializa los resultados en JSON.

    Args:
        current_user: Usuario resuelto por ``Depends(get_current_user)`` a partir del JWT.
        analyzer: Sesión ``B2BGraphAnalyzer`` inyectada por ``Depends(get_analyzer_instance)``.

    Returns:
        Documentos ordenados por ``issue_date`` descendente con campos: 
            ``document_id``, ``doc_type``, ``status``, ``issue_date``,
            ``due_date``, ``gross_amount``, ``total_amount``, ``currency``,
            ``discrepancy_flag``, ``payment_terms_days``, ``contract_type``.

    Raises:
        HTTPException: 401 si el token es inválido.
    """
    with analyzer._driver.session(database=settings.neo4j_database) as session:
        records = session.run(
            """
            MATCH (c:Company {company_id: $cid})-[:ISSUES]->(d:Document)
            RETURN d.document_id         AS document_id,
                   d.doc_type            AS doc_type,
                   d.status              AS status,
                   d.issue_date          AS issue_date,
                   d.due_date            AS due_date,
                   d.gross_amount        AS gross_amount,
                   d.total_amount        AS total_amount,
                   d.currency            AS currency,
                   d.discrepancy_flag    AS discrepancy_flag,
                   d.payment_terms_days  AS payment_terms_days,
                   d.contract_type       AS contract_type
            ORDER BY d.issue_date DESC
            LIMIT 200
            """,
            cid=current_user.company_id,
        ).data()

    return [
        {
            k: (
                v.iso_format() if hasattr(v, "iso_format")
                else v.isoformat() if hasattr(v, "isoformat")
                else v
            )
            for k, v in rec.items()
        }
        for rec in records
    ]


@router.patch("/api/documents/{doc_id}/status")
def update_document_status(
    doc_id: str,
    body: DocumentStatusUpdate,
    current_user: User = Depends(get_current_user),
    analyzer: B2BGraphAnalyzer = Depends(get_analyzer_instance),
) -> dict:
    """Actualiza el estado de un documento EDI propiedad de la empresa del usuario.

    La consulta a Neo4j incluye una validación de seguridad integrada para asegurar 
    que el usuario no pueda modificar documentos pertenecientes a otras empresas.

    Args:
        doc_id: Identificador único del documento (``document_id`` en Neo4j).
        body: Nuevo estado a aplicar; validado por ``DocumentStatusUpdate``.
        current_user: Usuario autenticado que realiza la petición.
        analyzer: Instancia del analizador con conexión activa a Neo4j.

    Returns:
        ``{"document_id": ..., "status": ...}`` con el valor actualizado.

    Raises:
        HTTPException: 403 si el documento no existe o pertenece a otra empresa.
        
    Note:
        Sin conexión al frontend. Previsto para desarrollos futuros.
    """
    with analyzer._driver.session(database=analyzer._database) as session:
        rec = session.run(
            """
            MATCH (c:Company {company_id: $cid})-[:ISSUES]->(d:Document {document_id: $doc_id})
            SET d.status = $status
            RETURN d.document_id AS document_id, d.status AS status
            """,
            cid=current_user.company_id,
            doc_id=doc_id,
            status=body.status,
        ).single()
    if not rec:
        raise HTTPException(status_code=403, detail="Documento no encontrado o sin permiso de acceso")
    return {"document_id": rec["document_id"], "status": rec["status"]}