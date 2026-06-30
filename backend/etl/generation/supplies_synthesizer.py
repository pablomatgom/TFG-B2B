"""Sintetizador de relaciones comerciales SUPPLIES entre empresas.

Genera ``rel_supplies.csv`` construyendo una red Scale-Free adaptada a la
topología LFR: las aristas intra-comunidad son más probables que las
inter-comunidad, y los nodos con mayor ``baseline_revenue`` tienen mayor
probabilidad de ser seleccionados como extremos de una arista.
"""
from __future__ import annotations

import argparse
import csv
import itertools
import math
import random
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
import logging         
from backend.etl.generation.csv_templates import CSV_SCHEMAS
from backend.core.utils import safe_float, pick

# =============================================================================
# CABECERA (Configuración y Modelos)
# =============================================================================
CONTRACT_TYPES = ["FRAME", "SPOT", "ANNUAL", "MULTIYEAR"]
PAYMENT_TERMS = [15, 30, 45, 60, 90]
PAYMENT_TERMS_WEIGHTS = [0.05, 0.45, 0.25, 0.20, 0.05]
SIMULATION_TODAY = date(2026, 1, 1)  # Reemplaza con date.today()


@dataclass(frozen=True)
class CompanyRecord:
    """Snapshot inmutable de atributos de empresa para la síntesis de SUPPLIES.

    Attributes:
        company_id: Identificador único de la empresa.
        node_role: Rol operativo: ``SUPPLIER``, ``BUYER`` o ``HYBRID``.
        region: Provincia.
        industry_code: Código NACE de la industria.
        size_band: Categoría de tamaño: ``micro``, ``pyme``, ``mid`` o ``enterprise``.
        baseline_revenue: Ingresos anuales base en euros (peso de selección).
        created_at: Fecha de creación (límite inferior de ``since_date``).
    """

    company_id: str
    node_role: str
    region: str
    industry_code: str
    size_band: str
    baseline_revenue: float
    created_at: date


# =============================================================================
# INTERFAZ PÚBLICA (CLI)
# =============================================================================
def get_supplies_parser() -> argparse.ArgumentParser:
    """Contiene solo los argumentos exclusivos de este módulo."""
    parser = argparse.ArgumentParser(add_help=False)
    # Creamos un grupo visual
    group = parser.add_argument_group("Opciones de rel_supplies.csv")
    group.add_argument("--avg-degree-supplies", type=int, default=7, help="Grado medio de salida por proveedor", metavar="N")
    return parser


# =============================================================================
# FUNCIÓN PRINCIPAL (MAIN)
# =============================================================================
def synthesize_rel_supplies_csv(output_file: Path, companies_csv: Path, avg_out_degree: int, mu: float, seed: int) -> Path:
    """Genera rel_supplies.csv con topología Scale-Free adaptada a comunidades LFR.

    Args:
        output_file: Ruta del fichero CSV de salida.
        companies_csv: Ruta al CSV de empresas generado previamente.
        avg_out_degree: Grado de salida medio deseado por proveedor.
        mu: Coeficiente de mezcla LFR para la conexión inter-comunidad.
            Debe ser ``0 <= mu < 1.0``.
        seed: Semilla para reproducibilidad.

    Returns:
        Ruta al fichero CSV escrito.

    Raises:
        ValueError: Si ``avg_out_degree <= 0``, ``0 <= mu < 1.0``, o no hay
            suficientes empresas con roles válidos para generar relaciones.
    """
    if avg_out_degree <= 0:
        raise ValueError("avg_out_degree debe ser > 0")
    if not (0.0 <= mu < 1.0):
        raise ValueError("El parámetro de mezcla 'mu' debe estar entre 0.0 y 1.0")

    rng = random.Random(seed)
    companies = load_companies(companies_csv)
    
    # Generación matemática de la topología del grafo
    edges = _generate_topology_edges(companies, avg_out_degree, mu, rng)
    
    # Generación de los atributos de negocio y escritura a disco
    _write_supplies_to_csv(output_file, edges, companies, rng)

    return output_file


# =============================================================================
# LÓGICA DE ALTO NIVEL (FUNCIONES AUXILIARES PARA LA FUNCIÓN PRINCIPAL)
# =============================================================================
def load_companies(companies_csv: Path) -> list[CompanyRecord]:
    """Carga el listado de empresas desde companies.csv.

    Args:
        companies_csv: Ruta al CSV de empresas generado por ``synthesize_companies_csv``.

    Returns:
        Lista de registros de empresa con roles validados.

    Raises:
        FileNotFoundError: Si ``companies_csv`` no existe.
        ValueError: Si el CSV no contiene registros válidos.
    """
    if not companies_csv.exists():
        raise FileNotFoundError(f"No existe el fichero de companies: {companies_csv}")

    # Apertura del CSV original de empresas
    companies: list[CompanyRecord] = []
    with companies_csv.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        # Extraemos solo los campos del .csv
        for row in reader:
            company_id = (pick(row, "company_id:ID(Company)", "company_id") or "").strip()
            node_role = (pick(row, "node_role:string", "node_role") or "").strip().upper()
            company_created_at = _parse_created_at(pick(row, "created_at:datetime", "created_at"))
            
            if not company_id:
                continue
            if node_role not in {"SUPPLIER", "BUYER", "HYBRID"}:
                node_role = "HYBRID"
            
            # Creacion del objeto inmutable
            companies.append(
                CompanyRecord(
                    company_id=company_id,
                    node_role=node_role,
                    region=(pick(row, "region:string", "region") or "").strip() or "UNKNOWN",
                    industry_code=(pick(row, "industry_code:string", "industry_code") or "").strip() or "UNKNOWN",
                    size_band=(pick(row, "size_band:string", "size_band") or "").strip() or "micro",
                    baseline_revenue=max(safe_float(pick(row, "baseline_revenue:float", "baseline_revenue"), 1.0), 1.0),
                    created_at=company_created_at,
                )
            )

    if not companies:
        raise ValueError("companies.csv no contiene registros válidos")

    return companies


def _generate_topology_edges(companies: list[CompanyRecord], avg_out_degree: int, mu: float, rng: random.Random) -> set[tuple[str, str]]:
    """Calcula las conexiones del grafo usando Scale-Free adaptado a comunidades LFR.

    Args:
        companies: Lista de empresas cargadas desde ``companies.csv``.
        avg_out_degree: Grado de salida medio deseado por proveedor.
        mu: Proporción de aristas inter-comunidad (coeficiente de mezcla LFR).
        rng: Generador aleatorio inicializado con la semilla global.

    Returns:
        Conjunto de pares ``(supplier_id, buyer_id)`` sin duplicados ni autoenlaces.
    """
    
    # Preparación de estructuras y cálculos base
    community_buckets, suppliers, buyers, community_keys = _build_community_structures(companies)
    target_edges, max_possible_edges = _calculate_edge_targets(len(companies), len(suppliers), len(buyers), avg_out_degree)
    pool_cum_weights, comm_supplier_cum_weights, comm_buyer_cum_weights = _precalculate_community_weights(community_buckets, community_keys)

    # Funciones Auxiliares para selección eficiente de candidatos y comunidades 
    def pick_candidate(key: tuple[str, str], role: str) -> CompanyRecord:
        """Selecciona un candidato en O(log N) usando búsqueda binaria."""
        pool = community_buckets[key][role]
        cum_weights = pool_cum_weights[(key, role)]
        # Fíjate que cambiamos 'weights=' por 'cum_weights='
        return rng.choices(pool, cum_weights=cum_weights, k=1)[0]

    def pick_community(role: str) -> tuple[str, str]:
        """Selecciona una comunidad en O(log C)."""
        cum_w = comm_supplier_cum_weights if role == "suppliers" else comm_buyer_cum_weights
        return rng.choices(community_keys, cum_weights=cum_w, k=1)[0]

    # Generación de Aristas (Bucle principal)
    edges: set[tuple[str, str]] = set()
    max_attempts = min(target_edges * 20, 1_000_000)
    attempts = 0
    
    while len(edges) < target_edges and attempts < max_attempts:
        attempts += 1
        
        # Mezcla LFR (Intra-comunidad vs Inter-comunidad)
        if rng.random() > mu:
            # Seleccion de supplier y buyer de Intra-comunidad.
            community_key = pick_community("buyers") 
            supplier = pick_candidate(community_key, "suppliers")
            buyer = pick_candidate(community_key, "buyers")
        else:
            supplier_community = pick_community("suppliers")
            buyer_community = pick_community("buyers")
            
            # Forzamos inter-comunidad si coinciden por azar
            if buyer_community == supplier_community and len(community_keys) > 1:
                alternative = [key for key in community_keys if key != supplier_community]
                buyer_community = rng.choice(alternative)
                
            supplier = pick_candidate(supplier_community, "suppliers")
            buyer = pick_candidate(buyer_community, "buyers")

        # Validación e inserción
        if supplier.company_id == buyer.company_id:
            continue
        
        edge = (supplier.company_id, buyer.company_id)
        if edge not in edges:
            edges.add(edge)
            
    # Verificación final
    if len(edges) < target_edges:
        achievement_ratio = (len(edges) / target_edges * 100) if target_edges > 0 else 0
        logging.warning(f"[Graph Saturation] Solo se alcanzaron {len(edges)}/{target_edges} aristas ({achievement_ratio:.1f}%). Máximo posible: {max_possible_edges}.")

    return edges


def _build_community_structures(companies: list[CompanyRecord]) -> tuple[dict, list, list, list]:
    """Agrupa las empresas en comunidades latentes y devuelve las estructuras necesarias.

    Args:
        companies: Lista de empresas cargadas desde ``companies.csv``.

    Returns:
        Tupla de cuatro elementos:
            - ``community_buckets``: dict ``{(attr, val): {"suppliers": [...], "buyers": [...]}}``
            - ``total_list_suppliers``: lista global de empresas con rol proveedor.
            - ``total_list_buyers``: lista global de empresas con rol comprador.
            - ``community_keys``: claves de comunidades válidas (≥1 proveedor y ≥1 comprador distintos).

    Raises:
        ValueError: Si no hay empresas con roles válidos o ninguna comunidad es válida.
    """
    community_buckets: dict[tuple[str, str], dict[str, list[CompanyRecord]]] = {}
    total_list_suppliers: list[CompanyRecord] = []
    total_list_buyers: list[CompanyRecord] = []
    
    # Clasificacion de empresas por rol y atributos de comunidad latente (región e industria)
    for company in companies:
        role_is_supplier = company.node_role in {"SUPPLIER", "HYBRID"}
        role_is_buyer = company.node_role in {"BUYER", "HYBRID"}

        if role_is_supplier:
            total_list_suppliers.append(company)
        if role_is_buyer:
            total_list_buyers.append(company)

        # Atributos de comunidad latente: región e industria. 
        keys = [
            ("region", company.region),
            ("industry", company.industry_code),
        ]
        
        for key in keys:
            bucket = community_buckets.setdefault(key, {"suppliers": [], "buyers": []})
            if role_is_supplier:
                bucket["suppliers"].append(company)
            if role_is_buyer:
                bucket["buyers"].append(company)

    if not total_list_suppliers or not total_list_buyers:
        raise ValueError("No hay suficientes empresas con roles válidos para generar relaciones.")

    # Filtrado de comunidades válidas (con al menos un proveedor y un comprador)
    def _is_valid_bucket(bucket: dict[str, list[CompanyRecord]]) -> bool:
        supplier_ids = {c.company_id for c in bucket["suppliers"]}
        buyer_ids = {c.company_id for c in bucket["buyers"]}
        
        if not supplier_ids or not buyer_ids:
            return False
            
        # Si hay un único proveedor y un único comprador y SON EL MISMO, es inválido (bucle). En caso contrario, es válido.
        if len(supplier_ids) == 1 and len(buyer_ids) == 1 and supplier_ids == buyer_ids:
            return False
            
        return True

    # Solo almacenamos las claves de las comunidades que son validas para la generación de relaciones.
    community_keys = [
        key for key, bucket in community_buckets.items() if _is_valid_bucket(bucket)
    ]
    if not community_keys:
        raise ValueError("No hay comunidades válidas para generar relaciones SUPPLIES")

    return community_buckets, total_list_suppliers, total_list_buyers, community_keys


def _calculate_edge_targets(total_companies: int, total_suppliers: int, total_buyers: int, avg_out_degree: int) -> tuple[int, int]:
    """Calcula el número objetivo de aristas y el máximo matemático posible, previniendo saturación.

    Args:
        total_companies: Número total de empresas en el grafo.
        total_suppliers: Número de empresas con rol proveedor (``SUPPLIER`` o ``HYBRID``).
        total_buyers: Número de empresas con rol comprador (``BUYER`` o ``HYBRID``).
        avg_out_degree: Grado de salida medio deseado por proveedor.

    Returns:
        Tupla ``(target_edges, max_possible_edges)``: objetivo real y máximo bipartito posible.

    Raises:
        ValueError: Si no hay proveedores o compradores suficientes para generar aristas.
    """
    max_possible_edges = total_suppliers * total_buyers
    
    if max_possible_edges == 0:
        raise ValueError("No hay suficientes proveedores o compradores para generar aristas (necesitas mínimo 1 de cada rol)")
    
    target_edges = max(total_companies, total_suppliers * avg_out_degree)
    
    if target_edges > max_possible_edges:
        target_edges = max_possible_edges
        saturation_ratio = (total_suppliers * avg_out_degree) / max_possible_edges
        logging.warning(f"[Graph Saturation] El grado medio solicitado es inalcanzable ({saturation_ratio*100:.1f}%). Limitando target a {target_edges}.")
        
    return target_edges, max_possible_edges


def _precalculate_community_weights(community_buckets: dict, community_keys: list) -> tuple[dict, list[float], list[float]]:
    """Precalcula los pesos acumulados por comunidad para selección eficiente O(log N).

    Args:
        community_buckets: Diccionario de comunidades con listas de proveedores y compradores.
        community_keys: Lista de claves de comunidades válidas sobre las que iterar.

    Returns:
        Tupla de tres elementos:
            - ``pool_cum_weights``: dict ``{(key, role): [cum_weight, ...]}`` por empresa.
            - ``comm_supplier_cum_weights``: pesos acumulados por comunidad (proveedores).
            - ``comm_buyer_cum_weights``: pesos acumulados por comunidad (compradores).
    """
    pool_cum_weights = {}
    
    for key, bucket in community_buckets.items():
        # Calculamos pesos base
        supplier_weights = [max(1.0, math.sqrt(c.baseline_revenue)) for c in bucket["suppliers"]]
        buyer_weights = [max(1.0, math.sqrt(c.baseline_revenue)) for c in bucket["buyers"]]
        
        # Acumulamos los pesos (solo una vez por comunidad)
        pool_cum_weights[(key, "suppliers")] = list(itertools.accumulate(supplier_weights))
        pool_cum_weights[(key, "buyers")] = list(itertools.accumulate(buyer_weights))

    # Para las comunidades, el peso total de la comunidad es el último valor de su lista acumulada
    comm_supplier_weights = [
        pool_cum_weights[(key, "suppliers")][-1] if pool_cum_weights[(key, "suppliers")] else 0 
        for key in community_keys
    ]
    comm_buyer_weights = [
        pool_cum_weights[(key, "buyers")][-1] if pool_cum_weights[(key, "buyers")] else 0 
        for key in community_keys
    ]

    # Acumulamos también los pesos de selección de comunidad
    comm_supplier_cum_weights = list(itertools.accumulate(comm_supplier_weights))
    comm_buyer_cum_weights = list(itertools.accumulate(comm_buyer_weights))

    return pool_cum_weights, comm_supplier_cum_weights, comm_buyer_cum_weights


def _write_supplies_to_csv(output_file: Path, edges: set[tuple[str, str]], companies: list[CompanyRecord], rng: random.Random) -> None:
    """Enriquece las aristas con atributos comerciales basados en lógica de negocio real.

    Args:
        output_file: Ruta del fichero CSV de salida.
        edges: Conjunto de pares ``(supplier_id, buyer_id)`` generados por la topología.
        companies: Lista de empresas para acceder a los atributos de cada extremo.
        rng: Generador aleatorio inicializado con la semilla global.
    """
    companies_dict = {c.company_id: c for c in companies}
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = CSV_SCHEMAS["rel_supplies.csv"]

    with output_file.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        for supplier_id, buyer_id in sorted(edges):
            supplier_obj = companies_dict[supplier_id]
            buyer_obj = companies_dict[buyer_id]
            
            # Logica de generación de atributos basada en características de las empresas y su relación temporal
            earliest_possible_date = max(supplier_obj.created_at, buyer_obj.created_at)
        
            contract_type = rng.choice(CONTRACT_TYPES)
            
            # El volumen acordado no puede superar el 15% de la facturación del menor de los dos por realismo.
            min_revenue_in_edge = min(supplier_obj.baseline_revenue, buyer_obj.baseline_revenue)
            max_logical_volume = min_revenue_in_edge * 0.15 
            agreed_volume = round(rng.uniform(0.01, 1.0) * max_logical_volume, 2)
            
            # El tiempo de entrega se ajusta según la industria y la proximidad geográfica, con excepciones para servicios digitales.
            if supplier_obj.industry_code in {"J62", "M71"}:
                lead_time = 0 # Servicios digitales/consultoría
            elif supplier_obj.region == buyer_obj.region:
                lead_time = rng.randint(1, 4)  # Misma Provincia
            else:
                lead_time = rng.randint(3, 10) # Tránsito Nacional
            
            # La fiabilidad se correlaciona con el tamaño de la empresa.    
            if supplier_obj.size_band in {"enterprise", "mid"}:
                reliability = round(rng.uniform(0.94, 0.999), 4) 
            else:
                reliability = round(rng.uniform(0.80, 0.96), 4)
            
            # La exclusividad es más probable en contratos FRAME o MULTIYEAR y cuando el proveedor no es más pequeño que el comprador.    
            is_exclusive = False
            if contract_type in {"FRAME", "MULTIYEAR"} and rng.random() > 0.85:
                # Un proveedor no puede ser exclusivo de un comprador si el comprador factura 100 veces más.
                if supplier_obj.baseline_revenue >= (buyer_obj.baseline_revenue * 0.10):
                    is_exclusive = True

            writer.writerow({
                ":START_ID(Company)": supplier_id,
                ":END_ID(Company)": buyer_id,
                "since_date:datetime": _random_since_date(rng, earliest_possible_date),
                "lead_time_days:int": lead_time,
                "reliability_score:float": reliability,
                "agreed_volume_baseline:float": max(agreed_volume, 500.0),
                "is_exclusive_supplier:boolean": is_exclusive,
                "payment_terms_agreed:int": rng.choices(PAYMENT_TERMS, weights=PAYMENT_TERMS_WEIGHTS, k=1)[0],
                "contract_type:string": contract_type,
                ":TYPE": "SUPPLIES",
            })


# =============================================================================
# FUNCIONES AUXILIARES (Helpers / Utils)
# =============================================================================

def _parse_created_at(raw_date: str | None) -> date:
    """Parsea la fecha de creación de la empresa desde el CSV.

    Args:
        raw_date: Cadena leída desde el campo ``created_at`` del CSV,
            o ``None`` / cadena vacía si el campo no está presente.

    Returns:
        Objeto ``date`` correspondiente, o una fecha de hace 5 años como fallback.
    """
    if raw_date and raw_date.strip():
        value = raw_date.strip().replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(value).date()
        except ValueError:
            pass
            
    # Fallback de seguridad con 5 años de antigüedad
    return SIMULATION_TODAY - timedelta(days=365 * 5)


def _random_since_date(rng: random.Random, start_date: date) -> str:
    """Genera una fecha de inicio de relación comercial aleatoria entre ``start_date`` y hoy.

    Args:
        rng: Generador aleatorio inicializado con la semilla global.
        start_date: Límite inferior (la más reciente de las fechas de creación de ambas empresas).

    Returns:
        Fecha en formato (``YYYY-MM-DD``) dentro del rango válido.
    """
    if start_date >= SIMULATION_TODAY:
        return SIMULATION_TODAY.isoformat()
        
    offset = rng.randint(0, (SIMULATION_TODAY - start_date).days)
    return (SIMULATION_TODAY - timedelta(days=offset)).isoformat()
