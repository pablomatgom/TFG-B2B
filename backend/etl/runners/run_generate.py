"""Orquestador de la Fase 1: generación de datos sintéticos en CSV.

Invoca los cinco sintetizadores en orden estricto de dependencia y persiste
un artefacto JSON con las métricas de la ejecución en ``data/processed/``.
"""
from __future__ import annotations
from datetime import datetime, UTC
from pathlib import Path
import logging

from backend.core.config import Settings
from backend.core.utils import write_step_artifact
from backend.etl.generation.csv_templates import create_csv_templates
from backend.etl.generation.companies_synthesizer import synthesize_companies_csv
from backend.etl.generation.documents_synthesizer import synthesize_documents_csv
from backend.etl.generation.products_synthesizer import synthesize_products_csv
from backend.etl.generation.rel_contains_synthesizer import synthesize_rel_contains_csv
from backend.etl.generation.supplies_synthesizer import synthesize_rel_supplies_csv

def run_generate(settings: Settings, csv_target: str, rows: int,
                 avg_degree_rel_supplies: int, avg_degree_documents: int, avg_degree_products: int,
                 gamma: float, beta: float, mu: float) -> Path:
    """Ejecuta la Fase 1 del pipeline: genera los CSVs sintéticos del modelo B2B.

    Invoca los sintetizadores en orden estricto (Companies → Supplies → Products
    → Documents → Contains) para respetar las dependencias entre ficheros.

    Args:
        settings: Configuración del sistema (rutas, semilla, conexión Neo4j).
        csv_target: ``"all"`` para generar todos los CSVs, o el nombre de un
            CSV concreto.
        rows: Número de empresas a generar, los demás datasets escalan a partir
            de este valor mediante los parámetros de grado medio.
        avg_degree_rel_supplies: Grado de salida medio en la red de suministros
            (aristas ``SUPPLIES`` por empresa proveedora).
        avg_degree_documents: Número medio de documentos EDI por par
            proveedor-comprador.
        avg_degree_products: Número medio de productos por proveedor.
        gamma: Exponente de la ley de potencia del grado (LFR).
        beta: Exponente de la ley de potencia del tamaño de comunidades (LFR).
        mu: Coeficiente de mezcla LFR: fracción de aristas inter-comunidad.

    Returns:
        Ruta al artefacto JSON de auditoría escrito en
            ``data/processed/generate_last_run.json``.
    """
    logging.info(f"[FASE 1] Generación Sintética iniciada. Target: '{csv_target}'")
    logging.info(f"         LFR Params: Seed={settings.seed}, \u03B3={gamma}, \u03B2={beta}, \u03BC={mu}")
    logging.info(f"         Dimensión: {rows} Empresas")
    logging.info(f"         Topología (Out-Degree Avg): Sup={avg_degree_rel_supplies}, Prod={avg_degree_products}, Doc={avg_degree_documents}")
    
    # Creación de los CSVs para el target indicado (puede ser "all" o un CSV específico)
    created_csvs = create_csv_templates(settings.data_synthetic_dir, csv_target)
    orden_estricto = {
        "companies.csv": 1,
        "rel_supplies.csv": 2,
        "products.csv": 3,
        "documents.csv": 4,
        "rel_contains.csv": 5,
    }
    # Reordenacion de la lista para cumplir las dependencias en cascada.
    created_csvs.sort(key=lambda path: orden_estricto.get(path.name, 99))
    
    # Parametrización de filas generadas para cada CSV
    companies_rows = 0
    products_rows = 0
    rel_supplies_rows = 0
    documents_rows = 0
    rel_contains_rows = 0
    cities_csv_path = settings.data_raw_dir / "municipios_espana.csv"
    companies_csv_path = settings.data_synthetic_dir / "companies.csv"
    rel_supplies_csv_path = settings.data_synthetic_dir / "rel_supplies.csv"
    products_csv_path = settings.data_synthetic_dir / "products.csv"
    documents_csv_path = settings.data_synthetic_dir / "documents.csv"

    # Iteración sobre los archivos que el usuario ha solicitado generar
    for csv_path in created_csvs:
        if csv_path.name == "companies.csv":
            synthesize_companies_csv(
                output_file=csv_path,
                cities_csv=cities_csv_path,
                rows=rows,
                seed=settings.seed,
                gamma=gamma,
                beta=beta,
                mu=mu,
            )
            companies_rows = rows
        if csv_path.name == "rel_supplies.csv":
            result_path = synthesize_rel_supplies_csv(
                output_file=csv_path,
                companies_csv=companies_csv_path,
                avg_out_degree=avg_degree_rel_supplies,
                mu=mu,
                seed=settings.seed,
            )
            with result_path.open("r", encoding="utf-8", newline="") as csv_file:
                rel_supplies_rows = max(sum(1 for _ in csv_file) - 1, 0)
        if csv_path.name == "products.csv":
            result_path = synthesize_products_csv(
                output_file=csv_path,
                companies_csv=companies_csv_path,
                rel_supplies_csv=rel_supplies_csv_path,
                avg_degree_products=avg_degree_products,
                seed=settings.seed,
            )
            with result_path.open("r", encoding="utf-8", newline="") as csv_file:
                products_rows = max(sum(1 for _ in csv_file) - 1, 0)
        if csv_path.name == "documents.csv":
            result_path = synthesize_documents_csv(
                output_file=csv_path,
                companies_csv=companies_csv_path,
                rel_supplies_csv=rel_supplies_csv_path,
                seed=settings.seed,
                avg_out_degree=avg_degree_documents,
            )
            with result_path.open("r", encoding="utf-8", newline="") as csv_file:
                documents_rows = max(sum(1 for _ in csv_file) - 1, 0)
        if csv_path.name == "rel_contains.csv":
            result_path = synthesize_rel_contains_csv(
                output_file=csv_path,
                documents_csv=documents_csv_path,
                products_csv=products_csv_path,
                seed=settings.seed,
            )
            with result_path.open("r", encoding="utf-8", newline="") as csv_file:
                rel_contains_rows = max(sum(1 for _ in csv_file) - 1, 0)
                
    # Preparación del payload con las métricas de la ejecución para guardarlo como artefacto
    payload = {
        "step": "generate",
        "status": "ok",
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "seed": settings.seed,
        "rows": rows,
        "avg_degree_rel_supplies": avg_degree_rel_supplies,
        "avg_degree_documents": avg_degree_documents,
        "avg_degree_products": avg_degree_products,
        "csv_target": csv_target,
        "companies_rows_generated": companies_rows,
        "products_rows_generated": products_rows,
        "rel_supplies_rows_generated": rel_supplies_rows,
        "documents_rows_generated": documents_rows,
        "rel_contains_rows_generated": rel_contains_rows,
        "generated_csv_files": [str(path) for path in created_csvs],
        "message": "CSV's generado/s. companies.csv, products.csv, rel_supplies.csv, documents.csv y rel_contains.csv incluyen datos sintéticos cuando aplica.",
    }
    return write_step_artifact(settings.data_processed_dir, "generate", payload)