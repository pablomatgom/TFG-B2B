from pydantic import BaseModel, field_validator
from typing import Optional


class CompanyProfileUpdate(BaseModel):
    """Actualización parcial del perfil de una empresa.

    Sólo los campos presentes en el cuerpo de la petición 
    se sobreescriben en el nodo ``Company`` de Neo4j al ser opcionales.

    Attributes:
        legal_name: Razón social de la empresa.
        city: Ciudad donde tiene sede la empresa.
        region: Comunidad autónoma o región administrativa.
        is_active: Si ``False``, la empresa queda marcada como inactiva en el grafo.
    
    Note:
        Modelo definido pero sin endpoint ni lógica de escritura en Neo4j.
        Previsto para desarrollo futuro.
    """

    legal_name: Optional[str] = None
    city:       Optional[str] = None
    region:     Optional[str] = None
    is_active:  Optional[bool] = None


_VALID_STATUSES = {
    "OPEN", "ACCEPTED", "PARTIALLY_CONFIRMED",
    "SHIPPED", "DELIVERED", "PARTIALLY_DELIVERED",
    "ISSUED", "SENT", "PAID", "OVERDUE",
}
"""Conjunto de transiciones de estado permitidas para un ``Document`` en el grafo."""


class DocumentStatusUpdate(BaseModel):
    """Cambio de estado de un documento EDI existente.

    Valida que el nuevo estado pertenezca al ciclo de vida permitido antes
    de ejecutar la modificación de Cypher en Neo4j.

    Attributes:
        status: Nuevo estado del documento. Debe ser uno de:
            ``OPEN``, ``ACCEPTED``, ``PARTIALLY_CONFIRMED``, ``SHIPPED``,
            ``DELIVERED``, ``PARTIALLY_DELIVERED``, ``ISSUED``, ``SENT``,
            ``PAID``, ``OVERDUE``.

    Raises:
        ValueError: Si ``status`` no pertenece a ``_VALID_STATUSES``.
    
    Note:
        Modelo definido pero sin endpoint ni lógica de escritura en Neo4j.
        Previsto para desarrollo futuro.
    """

    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Valida que el estado recibido pertenezca al ciclo de vida permitido.

        Args:
            v: Valor del campo ``status`` recibido en el cuerpo de la petición.

        Returns:
            El mismo valor ``v`` sin modificar si la validación es exitosa.

        Raises:
            ValueError: Si ``v`` no pertenece a ``_VALID_STATUSES``.
        """
        if v not in _VALID_STATUSES:
            raise ValueError(f"Estado '{v}' no válido. Opciones: {sorted(_VALID_STATUSES)}")
        return v