"""Seeding de usuarios demo en SQLite a partir de las empresas en Neo4j.

Se ejecuta como última fase del pipeline (``run_seed``) para poblar la base
de datos relacional con un usuario por empresa y un administrador global,
permitiendo probar el sistema de autenticación sin registros manuales.
"""

from __future__ import annotations

import logging

import bcrypt
from neo4j import GraphDatabase
from sqlalchemy.orm import Session

from backend.core.config import Settings
from backend.auth.db.database import Base, User, engine

logger = logging.getLogger(__name__)

DEMO_PASSWORD = "Demo1234!"


def seed(settings: Settings) -> dict:
    """Crea un usuario demo por empresa en Neo4j y un administrador global.

    Lee todos los nodos ``Company`` del grafo, genera un usuario SQLite por
    cada uno con email ``company{i}@demo.com`` y la contraseña compartida
    ``DEMO_PASSWORD``.  Si el usuario ya existe lo omite y siempre se garantiza
    la existencia de ``admin@demo.com`` con rol ``admin``.

    Args:
        settings: Configuración del sistema con credenciales de Neo4j y
            la ruta a la base de datos SQLite.

    Returns:
        Estadísticas de la operación con claves:

            - ``users_created``: número de usuarios nuevos insertados.
            - ``users_skipped``: número de usuarios que ya existían.
            - ``sqlite_db``: ruta absoluta al fichero ``users.db``.
            - ``demo_password``: contraseña usada para todos los usuarios.

    Raises:
        RuntimeError: Si no hay nodos ``Company`` en Neo4j (pipeline no
            ejecutado aún).
    """
    logger.info(f"Conectando a Neo4j en {settings.neo4j_uri}.")
    driver = GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )
    with driver.session(database=settings.neo4j_database) as session:
        records = session.run(
            "MATCH (c:Company) RETURN c.company_id AS id, c.legal_name AS name"
        ).data()
    driver.close()

    if not records:
        raise RuntimeError("No hay empresas en Neo4j. Ejecuta primero el pipeline.")

    logger.info(f"{len(records)} empresas encontradas. Creando usuarios demo.")

    Base.metadata.create_all(bind=engine)
    hashed_pw = bcrypt.hashpw(DEMO_PASSWORD.encode(), bcrypt.gensalt()).decode()

    users_created = 0
    users_skipped = 0

    with Session(engine) as db:
        for i, rec in enumerate(records):
            email = f"company{i}@demo.com"
            if db.query(User).filter(User.email == email).first():
                users_skipped += 1
                continue
            db.add(User(
                email=email,
                hashed_password=hashed_pw,
                company_id=rec["id"],
                full_name=rec["name"],
                role="company_user",
            ))
            users_created += 1

        if not db.query(User).filter(User.email == "admin@demo.com").first():
            db.add(User(
                email="admin@demo.com",
                hashed_password=hashed_pw,
                company_id="__admin__",
                full_name="Administrador",
                role="admin",
            ))
            logger.info("Usuario admin@demo.com creado")

        db.commit()

    logger.info(
        f"Seeding completado — creados: {users_created}, omitidos: {users_skipped}"
    )
    return {
        "users_created": users_created,
        "users_skipped": users_skipped,
        "sqlite_db": str(settings.sqlite_db_path),
        "demo_password": DEMO_PASSWORD,
    }