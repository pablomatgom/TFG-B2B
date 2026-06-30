"""Definición de esquemas CSV y utilidades para crear ficheros vacíos con cabeceras.

``CSV_SCHEMAS`` es la fuente única de verdad para los nombres y tipos de
columnas de cada CSV del modelo B2B.  ``create_csv_templates`` inicializa
los ficheros con sus cabeceras antes de que los sintetizadores los rellenen.
"""
from __future__ import annotations

import csv
from pathlib import Path

CSV_SCHEMAS: dict[str, list[str]] = {
    "companies.csv": [
        "company_id:ID(Company)",
        "legal_name:string",
        "tax_id:string",
        "edi_endpoint:string",
        "node_role:string",
        "country:string",
        "region:string",
        "city:string",
        "latitude:float",
        "longitude:float",
        "industry_code:string",
        "size_band:string",
        "baseline_revenue:float",
        "created_at:datetime",
        "is_active:boolean",
    ],
 
    "documents.csv": [
        "document_id:ID(Document)",
        "doc_type:string",
        "edi_standard:string",
        "version_number:int",
        "issue_date:datetime",
        "due_date:datetime",
        "status:string",
        "discrepancy_flag:boolean",
        "currency:string",
        "gross_amount:float",
        "tax_amount:float",
        "total_amount:float",
        "payment_terms_days:int",
        "contract_type:string",
        "lead_time_days:int",
        "created_at:datetime",
        "supplier_company_id:string",
        "buyer_company_id:string",
        "delay_days:int",
        "reference_id:string",
    ],
 
    "products.csv": [
        "product_id:ID(Product)",
        "sku:string",
        "hs_code:string",
        "name:string",
        "category:string",
        "unit:string",
        "base_price:float",
        "lead_time_baseline_days:int",
        "criticality:string",
        "is_substitutable:boolean",
        "supplier_company_id:string",
    ],
 
    "rel_supplies.csv": [
        ":START_ID(Company)",
        ":END_ID(Company)",
        "since_date:datetime",
        "lead_time_days:int",
        "reliability_score:float",
        "agreed_volume_baseline:float",
        "is_exclusive_supplier:boolean",
        "payment_terms_agreed:int",
        "contract_type:string",
        ":TYPE",
    ],
 
    "rel_contains.csv": [
        "line_id:string",
        "lot_number:string",
        "quantity:float",
        "unit_price:float",
        "discount_pct:float",
        "line_amount:float",
        "line_status:string",
        "expected_delivery_date:datetime",
        ":START_ID(Document)",
        ":END_ID(Product)",
        ":TYPE",
    ],
}


def _normalize_csv_name(name: str) -> str:
	value = name.strip().lower()
	if value.endswith(".csv"):
		value = value[:-4]
	return value


def get_available_targets() -> list[str]:
	"""Devuelve los nombres de los CSV disponibles (sin extensión), ordenados alfabéticamente.

	Returns:
		Nombres de los datasets disponibles (sin extensión), ordenados alfabéticamente.
	"""
	stems = [filename[:-4] for filename in CSV_SCHEMAS]
	return sorted(stems)


def resolve_csv_targets(csv_target: str) -> list[str]:
	"""Determina qué archivos CSV deben procesarse según el objetivo indicado.

	Args:
		csv_target: ``"all"`` para todos los datasets, o el nombre de un CSV
			concreto (con o sin extensión ``.csv``).

	Returns:
		Lista de nombres de fichero CSV ordenados.

	Raises:
		ValueError: Si ``csv_target`` no es ``"all"`` ni un nombre de CSV válido.
	"""
	value = _normalize_csv_name(csv_target)
	if value == "all":
		return sorted(CSV_SCHEMAS.keys())

	filename = f"{value}.csv"
	if filename not in CSV_SCHEMAS:
		available = ", ".join(["all", *get_available_targets()])
		raise ValueError(f"CSV objetivo inválido: '{csv_target}'. Valores válidos: {available}")

	return [filename]


def create_csv_templates(output_dir: Path, csv_target: str) -> list[Path]:
	"""Crea ficheros CSV vacíos con las cabeceras definidas en ``CSV_SCHEMAS``.

	Args:
		output_dir: Directorio de destino (``data/synthetic/``).
		csv_target: ``"all"`` para crear todos los CSVs, o el nombre de uno
			concreto (p. ej. ``"companies.csv"``).

	Returns:
		Lista de rutas a los ficheros CSV creados.

	Raises:
		ValueError: Si ``csv_target`` no es un selector válido.
	"""
	output_dir.mkdir(parents=True, exist_ok=True)
	targets = resolve_csv_targets(csv_target)
	created_files: list[Path] = []

	for filename in targets:
		target_path = output_dir / filename
		with target_path.open("w", encoding="utf-8", newline="") as csv_file:
			writer = csv.writer(csv_file)
			writer.writerow(CSV_SCHEMAS[filename])
		created_files.append(target_path)

	return created_files
