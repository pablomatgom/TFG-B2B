"""Capa de persistencia relacional para la autenticación de usuarios.

Define el modelo SQLAlchemy ``User``, inicializa el motor SQLite y expone
la dependencia FastAPI ``get_db``.  Las tablas se crean automáticamente al
importar este módulo (``Base.metadata.create_all``), por lo que no se
requiere ninguna migración manual.
"""
from __future__ import annotations

import datetime
from pathlib import Path

from sqlalchemy import Column, DateTime, Integer, String, create_engine
from typing import Generator
from sqlalchemy.orm import DeclarativeBase, Session

DB_PATH = Path(__file__).resolve().parents[3] / "data" / "users.db"

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False}, # Permite usar la misma conexión en hilos distintos (FastAPI maneja cada petición en un hilo).
)


class Base(DeclarativeBase):
    """Base declarativa de SQLAlchemy de la que heredan todos los modelos ORM."""


class User(Base):
    """Modelo que representa un usuario del sistema en SQLite.

    Cada usuario está vinculado a exactamente una empresa del grafo Neo4j
    mediante ``company_id``.  La contraseña nunca se almacena en texto
    plano, siempre se hashea con bcrypt.

    Attributes:
        id: Clave primaria autoincremental.
        email: Dirección de correo única; usada como ``sub`` en el JWT.
        hashed_password: Hash bcrypt de la contraseña del usuario.
        company_id: ID del nodo ``Company`` en Neo4j al que pertenece
            el usuario.
        full_name: Nombre completo opcional. Se inicializa con
            ``legal_name`` de la empresa durante el seeding.
        role: Nivel de acceso: ``"company_user"`` (por defecto) o ``"admin"``.
        is_active: ``1`` activo, ``0`` desactivado.  Los usuarios inactivos
            son rechazados por ``get_current_user``.
        created_at: Marca temporal de creación del registro.
    """

    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    email           = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    company_id      = Column(String, nullable=False)
    full_name       = Column(String, nullable=True)
    role            = Column(String, default="company_user")
    is_active       = Column(Integer, default=1)
    created_at      = Column(DateTime, default=datetime.timezone.utc)


Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Genera una sesión SQLAlchemy y la cierra al finalizar la petición.

    Diseñado como generador para usarse con ``Depends`` en FastAPI.
    La sesión se cierra en el bloque ``finally`` aunque el handler lance
    una excepción.

    Yields:
        Sesión SQLAlchemy activa vinculada a ``engine``.
    """
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()
