from __future__ import annotations

import argparse
import logging
from dataclasses import replace

from backend.core.config import load_settings
from backend.etl.generation.companies_synthesizer import get_companies_parser
from backend.etl.generation.documents_synthesizer import get_documents_parser
from backend.etl.generation.products_synthesizer import get_products_parser
from backend.etl.generation.supplies_synthesizer import get_supplies_parser

from backend.etl.runners.run_generate import run_generate
from backend.etl.runners.run_load import run_load
from backend.etl.runners.run_analyze import run_analyze
from backend.etl.runners.run_seed import run_seed
from backend.etl.runners.run_all import run_all

# =========================================================================
# CONFIGURACIÓN DEL SISTEMA DE MONITORIZACIÓN (LOGGING)
# =========================================================================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Silencia el ruido del driver de la base de datos, mostrando solo los mensajes de error.
logging.getLogger("neo4j.notifications").setLevel(logging.ERROR)

# =========================================================================
#  PUNTO DE ENTRADA PRINCIPAL (MAIN)
# =========================================================================
def main() -> None:
    """Punto de entrada principal del CLI de TFG-B2B.

    Parsea los argumentos de línea de comandos, carga la configuración desde
    ``.env`` y delega a uno de los cuatro subcomandos:
    ``generate`` → ``run_generate``, ``load`` → ``run_load``,
    ``analyze`` → ``run_analyze``, ``all`` → ``run_all``.
    Si se pasa ``--seed``, sobreescribe el valor de ``Settings.seed`` antes
    de invocar el runner correspondiente.
    """
    # Construcción del parser y lectura de argumentos
    parser = build_parser()
    args = parser.parse_args()

    # Carga de configuración global y sobreescritura con argumentos de línea de comandos si no se proporcionan
    settings = load_settings()
    
    seed_arg = getattr(args, 'seed', None)
    if seed_arg is not None:
        settings = replace(settings, seed=args.seed)

    # Aseguramos que los directorios de datos existen
    settings.ensure_data_directories()
    
    if args.command == "generate":
        artifact = run_generate(
            settings, 
            csv_target=args.csv, 
            rows=getattr(args, 'rows'), 
            avg_degree_products=getattr(args, 'avg_degree_products'),
            avg_degree_rel_supplies=getattr(args, 'avg_degree_supplies'), 
            avg_degree_documents=getattr(args, 'avg_degree_documents'),
            gamma=getattr(args, 'gamma'),
            beta=getattr(args, 'beta'),
            mu=getattr(args, 'mu'),
        )
        print(f"[OK] generate -> {artifact}")
        
    elif args.command == "load":
        artifact = run_load(
            settings, 
            batch_size_loader=getattr(args, 'batch_size_loader'),
            clear_db=getattr(args, 'clear_db', False) # Recuperamos el argumento
        )
        print(f"[OK] load -> {artifact}")
        
    elif args.command == "analyze":
        artifact = run_analyze(settings)
        print(f"[OK] analyze -> {artifact}")

    elif args.command == "seed":
        artifact = run_seed(settings)
        print(f"[OK] seed -> {artifact}")

    else:
        artifacts = run_all(
            settings,
            rows=getattr(args, 'rows'),
            avg_degree_products=getattr(args, 'avg_degree_products'),
            avg_degree_rel_supplies=getattr(args, 'avg_degree_supplies'),
            avg_degree_documents=getattr(args, 'avg_degree_documents'),
            gamma=getattr(args, 'gamma'),
            beta=getattr(args, 'beta'),
            mu=getattr(args, 'mu'),
            batch_size_loader=getattr(args, 'batch_size_loader'),
            clear_db=getattr(args, 'clear_db', False),
            skip_seed=getattr(args, 'skip_seed', False),
        )
        print("[OK] all")
        for artifact in artifacts:
            print(f"  - {artifact}")


# =========================================================================
#  DEFINICIÓN DEL INTERFAZ DE LÍNEA DE COMANDOS (CLI)
# =========================================================================
def build_parser() -> argparse.ArgumentParser:
    """Construye el parser principal con sus cinco subcomandos.

    Cada subcomando hereda argumentos de los parsers de los sintetizadores
    correspondientes (``get_companies_parser``, ``get_supplies_parser``, etc.)
    mediante ``parents=[...]``, evitando duplicar definiciones de argumentos.

    Returns:
        Parser configurado con subcomandos ``generate``, ``load``,
        ``analyze``, ``all`` y ``seed``.
    """
    
    parser = argparse.ArgumentParser(description="Pipeline TFG-B2B", formatter_class=CleanHelpFormatter)
    subparsers = parser.add_subparsers(
        dest="command", 
        required=True, 
        title="Comandos disponibles",
        help="Ejecuta uno de los comandos para ver su ayuda específica (ej. all -h)",
        metavar="{generate, load, analyze, all}"
    )


    # --- SUBCOMANDO PARA GENERATE ---
    parser_generate = subparsers.add_parser(
        "generate",
        help="Generación de datos sintéticos",
        formatter_class=CleanHelpFormatter,
        parents=[
            get_companies_parser(),
            get_products_parser(),
            get_supplies_parser(),
            get_documents_parser(),
        ]
    )
    parser_generate._optionals.title = "Opciones generales disponibles"
    parser_generate.add_argument(
        "--csv", 
        default="all", 
        help="Generación de CSV específico (Valores: all, companies, documents, products, rel_contains, rel_fulfills, rel_issues, rel_sent_to, rel_supplies)", 
        metavar="TARGET"
    )
    parser_generate.add_argument("--seed", type=int, default=None, help="Semilla global para generación", metavar="SEED")


    # --- SUBCOMANDO PARA LOAD ---
    parser_load = subparsers.add_parser(
        "load", 
        help="Carga de datos en BD",
        formatter_class=CleanHelpFormatter
    )
    parser_load._optionals.title = "Opciones generales disponibles"
    parser_load.add_argument("--batch_size_loader", type=int, default=10000, help="Filas por lote para Neo4j", metavar="N")
    parser_load.add_argument("--clear-db", action="store_true", help="Borra la base de datos antes de iniciar la carga masiva")
    
    
    # --- SUBCOMANDO PARA ANALYZE ---
    subparsers.add_parser(
        "analyze", 
        help="Análisis de topología",
        formatter_class=CleanHelpFormatter
    )


    # --- SUBCOMANDO PARA ALL ---
    parser_all = subparsers.add_parser(
        "all", 
        help="Ejecución del pipeline completo End-to-End",
        formatter_class=CleanHelpFormatter,
        parents=[
            get_companies_parser(),
            get_supplies_parser(),
            get_documents_parser(),
            get_products_parser(),
        ]
    )
    parser_all._optionals.title = "Opciones generales disponibles"
    parser_all.add_argument("--seed", type=int, default=None, help="Semilla global", metavar="SEED")
    parser_all.add_argument("--batch_size_loader", type=int, default=10000, help="Filas por lote para Neo4j", metavar="N")
    parser_all.add_argument("--clear-db", action="store_true", help="Borra la base de datos antes de iniciar la carga masiva")
    parser_all.add_argument("--skip-seed", action="store_true", help="Omite el seeding de usuarios demo en SQLite")


    # --- SUBCOMANDO PARA SEED ---
    subparsers.add_parser(
        "seed",
        help="Crea usuarios demo en SQLite a partir de las empresas en Neo4j",
        formatter_class=CleanHelpFormatter,
    )

    return parser


# =========================================================================
#  UTILIDADES DE FORMATO CLI
# =========================================================================
class CleanHelpFormatter(argparse.HelpFormatter):
    """Formateador personalizado para ensanchar columnas y ocultar los METAVAR en mayúsculas."""
    def __init__(self, prog):
        super().__init__(prog, max_help_position=45, width=100)
        
    def _format_action_invocation(self, action: argparse.Action) -> str:
        """Formatea la invocación de un argumento ocultando el metavar en mayúsculas.

        Para argumentos posicionales delega en el comportamiento estándar.
        Para opciones con ``--flag`` muestra únicamente las banderas, sin el
        metavar (p. ej. muestra ``--rows`` en lugar de ``--rows N``).

        Args:
            action: Acción del parser cuya invocación se va a formatear.

        Returns:
            Cadena formateada con las banderas del argumento, sin metavar.
        """
        if not action.option_strings:
            return super()._format_action_invocation(action)
        return ', '.join(action.option_strings)


# =========================================================================
# EJECUCIÓN DEL SCRIPT
# =========================================================================
if __name__ == "__main__":
    main()
