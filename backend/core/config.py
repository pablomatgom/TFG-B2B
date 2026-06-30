"""Configuración centralizada del sistema.

Toda la configuración se lee del entorno (variables de entorno o ``.env``)
a través de ``load_settings()``.  El objeto ``Settings`` resultante es
inmutable (``frozen=True``), lo que evita modificaciones accidentales
en tiempo de ejecución.  Para sobreescribir un campo usa
``dataclasses.replace(settings, field=value)``.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
	"""Configuración inmutable del sistema leída del entorno.

	Attributes:
		project_root: Raíz absoluta del repositorio (padre de ``backend/``).
		data_raw_dir: Directorio con datasets estáticos (``data/raw/``).
		data_synthetic_dir: Destino de los CSVs generados (``data/synthetic/``).
		data_processed_dir: Artefactos de ejecución por fase (``data/processed/``).
		data_export_dir: JSONs pre-computados servidos por la API (``data/export/``).
		sqlite_db_path: Ruta al fichero SQLite de usuarios (``data/users.db``).
		neo4j_uri: URI Bolt del servidor Neo4j (``NEO4J_URI``).
		neo4j_user: Usuario Neo4j (``NEO4J_USER``).
		neo4j_password: Contraseña Neo4j (``NEO4J_PASSWORD``).
		neo4j_database: Base de datos Neo4j activa (``NEO4J_DATABASE``).
		jwt_secret_key: Clave HMAC para firmar JWT (``JWT_SECRET_KEY``).
		seed: Semilla global para la generación pseudoaleatoria leída de
			``TFG_SEED``. ``None`` cuando la variable no está definida,
			lo que implica semilla aleatoria no determinista.
	"""

	project_root: Path
	data_raw_dir: Path
	data_synthetic_dir: Path
	data_processed_dir: Path
	data_export_dir: Path
	sqlite_db_path: Path
	neo4j_uri: str
	neo4j_user: str
	neo4j_password: str
	neo4j_database: str
	jwt_secret_key: str
	seed: int | None

	def ensure_data_directories(self) -> None:
		"""Crea los directorios de datos si no existen.

		Se llama una vez al inicio del pipeline para garantizar que las rutas
		de escritura existen antes de que los sintetizadores intenten abrir
		ficheros.
		"""
		self.data_raw_dir.mkdir(parents=True, exist_ok=True)
		self.data_synthetic_dir.mkdir(parents=True, exist_ok=True)
		self.data_processed_dir.mkdir(parents=True, exist_ok=True)
		self.data_export_dir.mkdir(parents=True, exist_ok=True)


def load_settings() -> Settings:
	"""Construye un objeto ``Settings`` a partir del entorno y rutas derivadas.

	Todas las variables de entorno tienen valores por defecto seguros para
	desarrollo local con Docker.  En producción deben sobreescribirse via
	``.env`` o variables del sistema.

	Returns:
		Instancia inmutable lista para usar en cualquier módulo.
	"""
	backend_dir = Path(__file__).resolve().parent
	project_root = backend_dir.parent.parent

	data_root = project_root / "data"
	data_raw_dir = data_root / "raw"
	data_synthetic_dir = data_root / "synthetic"
	data_processed_dir = data_root / "processed"
	data_export_dir = data_root / "export"

	return Settings(
		project_root=project_root,
		data_raw_dir=data_raw_dir,
		data_synthetic_dir=data_synthetic_dir,
		data_processed_dir=data_processed_dir,
		data_export_dir=data_export_dir,
		sqlite_db_path=data_root / "users.db",
		neo4j_uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
		neo4j_user=os.getenv("NEO4J_USER", "neo4j"),
		neo4j_password=os.getenv("NEO4J_PASSWORD", "AdminUser1234"),
		neo4j_database=os.getenv("NEO4J_DATABASE", "neo4j"),
		jwt_secret_key=os.getenv("JWT_SECRET_KEY", "change-me-in-production"),
		seed=int(_seed) if (_seed := os.getenv("TFG_SEED")) else None,
	)

