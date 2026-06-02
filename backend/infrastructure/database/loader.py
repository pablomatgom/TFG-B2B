from __future__ import annotations

import argparse
import csv
import time
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Any

from neo4j import Driver, GraphDatabase
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

logging.getLogger("neo4j.notifications").setLevel(logging.ERROR)

# --- CLASES Y FUNCIONES PARA CARGA MASIVA DE DATOS EN NEO4J ---
@dataclass(frozen=True)
class LoadStats:
    dataset: str
    file_path: str
    rows: int
    batches: int
    elapsed_seconds: float

    @property
    def rows_per_second(self) -> float:
        if self.elapsed_seconds <= 0:
            return float(self.rows)
        return self.rows / self.elapsed_seconds


class Neo4jBulkLoader:
    """Carga masiva por lotes para nodos y relaciones del modelo B2B."""

    CONSTRAINTS_AND_INDEXES = [    
        # --- RESTRICCIONES DE UNICIDAD (Para MERGE rápido) ---
        "CREATE CONSTRAINT company_id_unique IF NOT EXISTS FOR (c:Company) REQUIRE c.company_id IS UNIQUE",
        "CREATE CONSTRAINT product_id_unique IF NOT EXISTS FOR (p:Product) REQUIRE p.product_id IS UNIQUE",
        "CREATE CONSTRAINT document_id_unique IF NOT EXISTS FOR (d:Document) REQUIRE d.document_id IS UNIQUE",
        "CREATE CONSTRAINT timebucket_id_unique IF NOT EXISTS FOR (t:TimeBucket) REQUIRE t.date IS UNIQUE",
        
        # --- ÍNDICES PARA ANALÍTICA Y FILTRADO ---
        "CREATE INDEX company_role_idx IF NOT EXISTS FOR (c:Company) ON (c.node_role)",
        "CREATE INDEX company_region_idx IF NOT EXISTS FOR (c:Company) ON (c.region)",
        "CREATE INDEX company_industry_idx IF NOT EXISTS FOR (c:Company) ON (c.industry_code)", 
        "CREATE INDEX product_hs_code_idx IF NOT EXISTS FOR (p:Product) ON (p.hs_code)",
        "CREATE INDEX product_criticality_idx IF NOT EXISTS FOR (p:Product) ON (p.criticality)",
        "CREATE INDEX document_type_idx IF NOT EXISTS FOR (d:Document) ON (d.doc_type)",
        "CREATE INDEX document_contract_idx IF NOT EXISTS FOR (d:Document) ON (d.contract_type)",
        "CREATE INDEX document_discrepancy_idx IF NOT EXISTS FOR (d:Document) ON (d.discrepancy_flag)",
        "CREATE INDEX document_type_discrepancy_idx IF NOT EXISTS FOR (d:Document) ON (d.doc_type, d.discrepancy_flag)",
    ]

    LOAD_QUERIES: dict[str, str] = {
        "companies.csv": """
            UNWIND $rows AS row
            // OPTIMIZACIÓN: CREATE en lugar de MERGE evita el Read-Lock
            CREATE (c:Company {company_id: row.company_id})
            SET c.legal_name = row.legal_name,
                c.tax_id = row.tax_id,
                c.edi_endpoint = row.edi_endpoint,
                c.node_role = row.node_role,
                c.country = row.country,
                c.region = row.region,
                c.city = row.city,
                c.latitude = toFloat(coalesce(row.latitude, 0.0)),
                c.longitude = toFloat(coalesce(row.longitude, 0.0)),
                c.industry_code = row.industry_code,
                c.size_band = row.size_band,
                c.baseline_revenue = toFloat(coalesce(row.baseline_revenue, 0.0)),
                c.created_at = CASE WHEN coalesce(row.created_at, "") = "" THEN c.created_at ELSE datetime(row.created_at) END,
                c.is_active = toBoolean(coalesce(row.is_active, "true"))
        """,
        
        "rel_supplies.csv": """
            UNWIND $rows AS row
            MATCH (supplier:Company {company_id: row.supplier_company_id})
            MATCH (buyer:Company {company_id: row.buyer_company_id})
            // Mantenemos MERGE para relaciones por seguridad transaccional
            MERGE (supplier)-[r:SUPPLIES]->(buyer)
            SET r.since_date = CASE WHEN coalesce(row.since_date, "") = "" THEN r.since_date ELSE date(row.since_date) END,
                r.lead_time_days = toInteger(coalesce(row.lead_time_days, 0)),
                r.reliability_score = toFloat(coalesce(row.reliability_score, 0.0)),
                r.agreed_volume_baseline = toFloat(coalesce(row.agreed_volume_baseline, 0.0)),
                r.is_exclusive_supplier = toBoolean(coalesce(row.is_exclusive_supplier, "false")),
                r.payment_terms_agreed = toInteger(coalesce(row.payment_terms_agreed, 0)),
                r.contract_type = row.contract_type
        """,

        "products.csv": """
            UNWIND $rows AS row
            CREATE (p:Product {product_id: row.product_id})
            SET p.sku = row.sku,
                p.hs_code = row.hs_code,
                p.name = row.name,
                p.category = row.category,
                p.unit = row.unit,
                p.base_price = toFloat(row.base_price),
                p.lead_time_baseline_days = toInteger(row.lead_time_baseline_days),
                p.criticality = row.criticality,
                p.is_substitutable = toBoolean(toLower(row.is_substitutable))

            WITH p, row
            MATCH (supplier:Company {company_id: row.supplier_company_id})
            CREATE (supplier)-[:SELLS]->(p)
        """,
        
        "documents.csv": """
            UNWIND $rows AS row
            
            // OPTIMIZACIÓN: Crear el nodo Document directo a disco
            CREATE (doc:Document {document_id: row.document_id})
            SET doc.doc_type = row.doc_type,
                doc.edi_standard = row.edi_standard,
                doc.version_number = toInteger(row.version_number),
                doc.issue_date = CASE WHEN coalesce(row.issue_date, "") <> "" THEN date(row.issue_date) ELSE null END,
                doc.due_date = CASE WHEN coalesce(row.due_date, "") <> "" THEN date(row.due_date) ELSE null END,
                doc.status = row.status,
                doc.discrepancy_flag = toBoolean(toLower(row.discrepancy_flag)),
                doc.currency = row.currency,
                doc.gross_amount = toFloat(row.gross_amount),
                doc.tax_amount = toFloat(row.tax_amount),
                doc.total_amount = toFloat(row.total_amount),
                doc.payment_terms_days = toInteger(row.payment_terms_days),
                doc.contract_type = row.contract_type,
                doc.lead_time_days = toInteger(row.lead_time_days)

            // Relación con empresas (ISSUES / SENT_TO)
            WITH doc, row
            MATCH (supplier:Company {company_id: row.supplier_company_id})
            MATCH (buyer:Company {company_id: row.buyer_company_id})

            // Utilizacion de CREATE para evita el read-lock sobre los supernodos
            CREATE (supplier)-[r_issues:ISSUES {created_at: datetime(row.created_at)}]->(doc)
            CREATE (doc)-[:SENT_TO]->(buyer)

            // Creacion de conexion con TIME_BUCKET
            WITH doc, row
            CALL (doc, row) {
                WITH doc, row WHERE coalesce(row.issue_date, "") <> ""
                WITH doc, date(row.issue_date) AS dDate
                MERGE (tb:TimeBucket {date: dDate})
                ON CREATE SET tb.year = dDate.year, tb.month = dDate.month, tb.day = dDate.day
                MERGE (doc)-[:Issue_on]->(tb)
            }

            // TRAZABILIDAD DOCUMENTAL (FULFILLS)
            WITH doc, row
            CALL (doc, row) {
                WITH doc, row WHERE row.reference_id <> ""
                MATCH (orig:Document {document_id: row.reference_id})
                CREATE (doc)-[f:FULFILLS {delay_days: toInteger(row.delay_days)}]->(orig)
            }
        """,

        "rel_contains.csv": """
            UNWIND $rows AS row
            MATCH (doc:Document {document_id: row.document_id})
            MATCH (prod:Product {product_id: row.product_id})
            
            // Utilizacion de CREATE por optimizacion de escritura (No duplicados en CSV)
            CREATE (doc)-[r:CONTAINS {line_id: row.line_id}]->(prod)
            SET r.lot_number = row.lot_number,
                r.quantity = toFloat(row.quantity),
                r.unit_price = toFloat(row.unit_price),
                r.discount_pct = toFloat(row.discount_pct),
                r.line_amount = toFloat(row.line_amount),
                r.line_status = row.line_status,
                r.expected_delivery_date = CASE WHEN coalesce(row.expected_delivery_date, "") = "" THEN null ELSE date(row.expected_delivery_date) END
        """
    }

    REQUIRED_DATASETS = ("companies.csv", "rel_supplies.csv", "products.csv", "documents.csv", "rel_contains.csv")

    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str, 
                 neo4j_database: str, batch_size: int,) -> None:
        """Inicialización del loader con parámetros de conexión y configuración."""
        self.neo4j_database = neo4j_database
        self.batch_size = max(batch_size, 1)
        self._driver: Driver = GraphDatabase.driver(
            neo4j_uri,
            auth=(neo4j_user, neo4j_password),
        )

    def close(self) -> None:
        """ Cierre de la conexión al driver de Neo4j y liberar recursos"""
        self._driver.close()

    def __enter__(self) -> "Neo4jBulkLoader":
        """ Permite usar el loader como un contexto (with statement) para asegurar el cierre correcto de recursos."""
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        """ Cierre automático del driver al salir del contexto, incluso si ocurre una excepción."""
        self.close()

    def verify_connection(self) -> None:
        """ Verificación de la conectividad con la base de datos Neo4j, lanzando una excepción si no se puede conectar."""
        self._driver.verify_connectivity()
        
    def clear_database(self) -> None:
        """Elimina todos los nodos y relaciones de la base de datos de forma segura por lotes."""
        logging.info("Iniciando borrado completo de la base de datos (nodos y relaciones)...")
        # Borrado en lotes transaccionales para grafos masivos
        query = """
            MATCH (n)
            CALL {
                WITH n
                DETACH DELETE n
            } IN TRANSACTIONS OF 10000 ROWS
        """
        try:
            with self._driver.session(database=self.neo4j_database) as session:
                session.run(query).consume()
            logging.info("Base de datos borrada con éxito. El grafo está vacío.")
        except Exception as e:
            logging.error(f"Error al intentar borrar la base de datos: {e}")
            raise e

    def create_constraints_and_indexes(self) -> None:
        logging.info("Creando constraints e índices en Neo4j...")
        with self._driver.session(database=self.neo4j_database) as session:
            for query in self.CONSTRAINTS_AND_INDEXES:
                session.run(query).consume()

    def load_from_directory(self, csv_dir: Path) -> dict[str, Any]:
        per_dataset: list[dict[str, Any]] = []
        total_rows = 0
        total_seconds = 0.0

        # Importante: Garantizar el orden de carga (Empresas -> Contratos -> Documentos)
        for dataset_name in self.REQUIRED_DATASETS:
            file_path = csv_dir / dataset_name
            if not file_path.exists():
                logging.warning(f"No se encontró el archivo {dataset_name}. Saltando...")
                continue

            logging.info(f"Cargando dataset: {dataset_name}...")
            stats = self._load_csv_dataset(dataset_name=dataset_name, file_path=file_path)
            total_rows += stats.rows
            total_seconds += stats.elapsed_seconds
            per_dataset.append({
                "dataset": stats.dataset,
                "rows": stats.rows,
                "elapsed_seconds": round(stats.elapsed_seconds, 4),
                "rows_per_second": round(stats.rows_per_second, 2),
            })
            logging.info(f"Terminado {dataset_name}: {stats.rows} filas en {stats.elapsed_seconds:.2f}s ({stats.rows_per_second:.0f} rows/s)")

        global_rps = (total_rows / total_seconds) if total_seconds > 0 else float(total_rows)
        return {
            "datasets_loaded": len(per_dataset),
            "total_rows": total_rows,
            "total_elapsed_seconds": round(total_seconds, 4),
            "global_rows_per_second": round(global_rps, 2),
            "per_dataset": per_dataset,
        }

    def _load_csv_dataset(self, dataset_name: str, file_path: Path) -> LoadStats:
        query = self.LOAD_QUERIES[dataset_name]
        started = time.perf_counter()
        rows = 0
        batches = 0

        with self._driver.session(database=self.neo4j_database) as session:
            for batch in self._iter_csv_batches(file_path):
                if not batch: continue
                session.execute_write(self._write_batch, query, batch)
                rows += len(batch)
                batches += 1

        elapsed_seconds = time.perf_counter() - started
        return LoadStats(dataset_name, str(file_path), rows, batches, elapsed_seconds)

    @staticmethod
    def _write_batch(tx: Any, query: str, rows: list[dict[str, str | None]]) -> None:
        tx.run(query, rows=rows).consume()

    @staticmethod
    def _clean_key(key: str) -> str:
        """Limpia los sufijos de Neo4j admin (ej. 'company_id:ID(Company)' -> 'company_id')"""
        if not key: return ""
        
        # Mapeos explícitos para las aristas según los templates
        if key == ":START_ID(Company)": return "supplier_company_id"
        if key == ":END_ID(Company)": return "buyer_company_id"
        if key == ":START_ID(Document)": return "document_id"
        if key == ":END_ID(Product)": return "product_id"
        if key == ":TYPE": return "type"
        
        # Quitar todo lo que va después de los dos puntos (ej. legal_name:string -> legal_name)
        return key.split(":")[0]

    def _iter_csv_batches(self, file_path: Path) -> Iterator[list[dict[str, str | None]]]:
        batch: list[dict[str, str | None]] = []
        with file_path.open("r", encoding="utf-8", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            
            # Limpiar y mapear las cabeceras sobre la marcha
            if reader.fieldnames:
                clean_fieldnames = [self._clean_key(f) for f in reader.fieldnames]
                reader.fieldnames = clean_fieldnames
                
            for row in reader:
                # Si está vacío, enviamos None para que Neo4j reciba un 'null' real
                normalized = {key: (value.strip() if value and value.strip() else None) for key, value in row.items()}
                batch.append(normalized)
                if len(batch) >= self.batch_size:
                    yield batch
                    batch = []
        if batch:
            yield batch
