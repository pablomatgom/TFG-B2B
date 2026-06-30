from pydantic import BaseModel
from typing import Optional


class LoginRequest(BaseModel):
    """Payload para la autenticación de un usuario existente.

    Attributes:
        email: Dirección de correo electrónico del usuario.
        password: Contraseña en texto plano (se verifica contra el hash almacenado).
    """

    email: str
    password: str


class TokenResponse(BaseModel):
    """Respuesta emitida tras un login o registro exitoso.

    Attributes:
        access_token: JWT firmado con la clave del .env del servidor.
        token_type: Esquema de autenticación HTTP, siempre ``"bearer"``.
    """

    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    """Representación pública de un usuario.

    Attributes:
        id: Identificador numérico interno del usuario en la base de datos relacional.
        email: Dirección de correo electrónico única del usuario.
        company_id: ID de la empresa B2B a la que pertenece el usuario (nodo ``Company`` en Neo4j).
        full_name: Nombre completo opcional para personalización de la interfaz.
        role: Rol de acceso. Valores: ``"admin"`` o ``"company_user"``.
    """

    id: int
    email: str
    company_id: str
    full_name: Optional[str] = None
    role: str

    model_config = {"from_attributes": True}


class RegisterRequest(BaseModel):
    """Payload para registrar un nuevo usuario en el sistema.

    Attributes:
        email: Dirección de correo electrónico (debe ser única).
        password: Contraseña en texto plano; el backend la hashea antes de persistirla.
        company_id: ID de la empresa B2B que representa este usuario.
        full_name: Nombre completo opcional.
        role: Rol asignado al crear la cuenta; por defecto ``"company_user"``.
        
    Note:
        Endpoint definido en el router pero no desarrollado en el frontend.
        Previsto para desarrollos futuros.
    """

    email: str
    password: str
    company_id: str
    full_name: Optional[str] = None
    role: Optional[str] = "company_user"