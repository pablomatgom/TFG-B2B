"""Dependencias y utilidades compartidas por los routers de la API.

Centraliza tres responsabilidades:

- **Autenticación JWT**: constantes y la dependencia ``get_current_user``.
- **Conexión a Neo4j**: la dependencia ``get_analyzer_instance`` gestiona
  el ciclo de vida del driver por petición.
- **Helpers de serialización**: ``read_json`` y ``neo4j_to_dict`` evitan
  duplicar lógica de lectura de ficheros y conversión de tipos Neo4j.

Todas las constantes de configuración (``SECRET_KEY``, ``EXPORT_DIR``) se
leen desde ``Settings`` vía ``load_settings()``, que es la única fuente de
verdad para valores de entorno.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Generator

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.core.config import load_settings
from backend.etl.analytics.analyzer import B2BGraphAnalyzer
from backend.auth.db.database import User, get_db

logger = logging.getLogger(__name__)

# ── JWT constants (shared with routers/auth.py) ────────────────
_settings    = load_settings()
SECRET_KEY   = _settings.jwt_secret_key
ALGORITHM    = "HS256"
EXPIRE_HOURS = 24

# ── Pre-computed export directory   ────────────────────────────
EXPORT_DIR = _settings.data_export_dir

_bearer = HTTPBearer()


# ── FastAPI dependencies ───────────────────────────────────────

def get_analyzer_instance() -> Generator[B2BGraphAnalyzer, None, None]:
    """Crea un ``B2BGraphAnalyzer`` conectado y lo cierra al finalizar la petición.

    Diseñado como generador para usarse con ``Depends``.  El bloque
    ``finally`` garantiza que el driver Neo4j se cierra aunque el handler
    lance una excepción.

    Yields:
        B2BGraphAnalyzer: Instancia lista para ejecutar consultas Cypher.
    """
    settings = load_settings()
    analyzer = B2BGraphAnalyzer(
        neo4j_uri=settings.neo4j_uri,
        neo4j_user=settings.neo4j_user,
        neo4j_password=settings.neo4j_password,
        neo4j_database=settings.neo4j_database,
    )
    try:
        yield analyzer
    finally:
        analyzer.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """Decodifica el JWT Bearer y devuelve el usuario activo desde SQLite.

    FastAPI extrae automáticamente el token de la cabecera
    ``Authorization: Bearer <token>`` gracias a ``HTTPBearer``.

    Args:
        credentials: Token Bearer extraído por ``HTTPBearer``.
        db: Sesión SQLAlchemy inyectada por FastAPI.

    Returns:
        Instancia del usuario autenticado y activo.

    Raises:
        HTTPException: 401 si el token está expirado, es inválido o el
            usuario no existe / está desactivado en SQLite.
    """
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado - vuelve a iniciar sesión")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")

    user = db.query(User).filter(User.email == payload["sub"], User.is_active == 1).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado o desactivado")
    return user


# ── Shared helpers ─────────────────────────────────────────────

def read_json(filename: str, default: Any = None) -> Any:
    """Lee un fichero JSON pre-computado del directorio de exportación.

    Si el fichero no existe, devuelve ``default`` en lugar de lanzar una
    excepción, permitiendo que los endpoints respondan vacíos
    en lugar de con un 500.

    Args:
        filename: Nombre del fichero dentro de ``EXPORT_DIR``.
        default: Valor de retorno si el fichero no existe.  Si es ``None``
            se devuelve un dict vacío ``{}``.

    Returns:
        Contenido deserializado del JSON, o ``default`` si no existe.
    """
    path = EXPORT_DIR / filename
    if not path.exists():
        return default if default is not None else {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def neo4j_to_dict(node: Any) -> dict:
    """Convierte la consulta de Neo4j en un diccionario serializable a JSON.

    Args:
        node: Nodo Neo4j devuelto por el driver (``neo4j.graph.Node``).

    Returns:
        Propiedades del nodo con valores JSON-serializables.
    """
    result = {}
    for k, v in dict(node).items():
        if hasattr(v, "iso_format"):
            result[k] = v.iso_format()
        elif hasattr(v, "isoformat"):
            result[k] = v.isoformat()
        else:
            result[k] = v
    return result