"""Sintetizador de empresas con topología LFR y anclaje geográfico real.

Genera ``companies.csv`` usando el modelo Lancichinetti-Fortunato-Radicchi (LFR)
para producir comunidades con distribuciones de grado power-law realistas.
Los municipios reales de ``data/raw/municipios_espana.csv`` anclan la ubicación
geográfica de cada empresa dentro de su comunidad.
"""
from __future__ import annotations
import argparse
import csv
import logging
import random
from dataclasses import dataclass
from datetime import timezone
from pathlib import Path
from faker import Faker
from backend.etl.generation.csv_templates import CSV_SCHEMAS
from backend.core.utils import safe_float, safe_int

# =============================================================================
#  CABECERA (Configuración y Modelos)
# =============================================================================
INDUSTRY_CODES = ["C10","C13", "C20", "C22", "C25", "C26", 
                  "C28", "C29", "G46", "H52", "J62", "M71"] # Estándar NACE Rev. 2
SIZE_BANDS = ["micro", "pyme", "mid", "enterprise"]
NODE_ROLES = ["SUPPLIER", "BUYER", "HYBRID"]
GEO_JITTER_DEG = 0.015
fake = Faker("es_ES")


@dataclass(frozen=True)
class MunicipalityPoint:
    """Punto geográfico de un municipio español ponderado por población.

    Attributes:
        province: Nombre de la provincia (clave de comunidad latente).
        municipality: Nombre del municipio.
        lat: Latitud en grados decimales.
        lon: Longitud en grados decimales.
        population: Habitantes censados, usado como peso en el muestreo geográfico.
    """

    province: str
    municipality: str
    lat: float
    lon: float
    population: int


@dataclass(frozen=True)
class LFRProfile:
    """Perfil LFR asignado a cada empresa durante la síntesis.

    Attributes:
        community_id: Identificador de la comunidad LFR a la que pertenece.
        anchor_province: Provincia de anclaje para sesgar la ubicación
            geográfica de la empresa dentro de su comunidad.
        preferred_industries: Tupla de códigos NACE preferidos por la comunidad.
        degree_propensity: Grado de conectividad esperado del nodo en la red
            (muestreado con distribución Pareto controlada por ``gamma``).
        mixing_mu: Proporción de aristas inter-comunidad para este nodo
            (muestreada con distribución Beta centrada en ``mu``).
    """

    community_id: int
    anchor_province: str
    preferred_industries: tuple[str, ...]
    degree_propensity: float
    mixing_mu: float


# =============================================================================
#  INTERFAZ PÚBLICA (CLI)
# =============================================================================
def get_companies_parser() -> argparse.ArgumentParser:
    """Contiene solo los argumentos exclusivos de este módulo."""
    parser = argparse.ArgumentParser(add_help=False)
    # Creamos un grupo visual
    group = parser.add_argument_group("Opciones de companies.csv")
    group.add_argument("--rows", type=int, default=200, help="Número de empresas a sintetizar", metavar="N")
    # Hiperparámetros LFR configurables
    group.add_argument("--gamma", type=float, default=2.4, help="Gamma: Exponente de la distribución de grados (Grado de nodos)", metavar="N")
    group.add_argument("--beta", type=float, default=1.8, help="Beta: Exponente de la distribución de tamaños de comunidad", metavar="N")
    group.add_argument("--mu", type=float, default=0.30, help="Mixing parameter (mu): Proporción de enlaces inter-comunidad", metavar="N")
    return parser


# =============================================================================
#  FUNCIÓN PRINCIPAL (MAIN)
# =============================================================================
def synthesize_companies_csv(output_file: Path, cities_csv: Path, rows: int, seed: int,
                             gamma: float, beta: float, mu: float) -> Path:
    """Genera companies.csv con topología LFR y anclaje geográfico real.

    Los tamaños de comunidad se calculan dinámicamente:
    ``min_comm = max(4, rows^0.40)`` y ``max_comm = max(min_comm+5, rows//5)``.

    Args:
        output_file: Ruta del fichero CSV de salida.
        cities_csv: Ruta al CSV de municipios españoles (``municipios_espana.csv``).
        rows: Número de empresas (nodos ``Company``) a generar.
        seed: Semilla para reproducibilidad.
        gamma: Exponente de la ley de potencias para la distribución de grados
            del modelo LFR. Debe ser ``> 1.0``.
        beta: Exponente de la ley de potencias para el tamaño de las comunidades
            LFR. Debe ser ``> 1.0``.
        mu: Coeficiente de mezcla LFR para la conexión inter-comunidad.
            Debe ser ``0 <= mu < 1.0``.

    Returns:
        Ruta al fichero CSV escrito.

    Raises:
        ValueError: Si ``rows <= 0``, ``gamma`` o ``beta ≤ 1.0``, o ```0 <= mu < 1.0``.
    """
    if rows <= 0:
        logging.error("El número de filas solicitado es inválido (<= 0).")
        raise ValueError("El número de filas debe ser > 0")
    if gamma <= 1.0 or beta <= 1.0:
        logging.error("Los hiperparámetros topológicos Gamma y Beta deben ser estrictamente > 1.0")
        raise ValueError("gamma y beta deben ser > 1.0")
    if not (0 <= mu <= 1):
        logging.error("El mixing parameter (mu) está fuera del rango probabilístico [0, 1].")
        raise ValueError("mu (mixing parameter) debe estar entre 0.0 y 1.0")

    min_comm = max(4, int(rows ** 0.40))
    max_comm = max(min_comm + 5, rows // 5)
    logging.info(f"         Comunidades LFR (calculado): min={min_comm}, max={max_comm}")

    # Inicializacion de motores aleatorios (estándar y el de Faker) con la semilla
    rng = random.Random(seed)
    Faker.seed(seed)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Carga de datos geográficos de municipios y generación de perfiles LFR
    municipalities, municipality_weights = load_municipalities(cities_csv)
    profiles = _build_lfr_profiles(
        rows=rows, municipalities=municipalities, municipality_weights=municipality_weights, rng=rng,
        gamma=gamma, beta=beta, mu=mu, min_comm=min_comm, max_comm=max_comm
    )

    cities_by_province: dict[str, list[MunicipalityPoint]] = {}
    weights_by_province: dict[str, list[int]] = {} 

    for municipality in municipalities:
        cities_by_province.setdefault(municipality.province, []).append(municipality)
        
    for prov, cities_list in cities_by_province.items():
        weights_by_province[prov] = [max(point.population, 1) for point in cities_list]
        
    fieldnames = CSV_SCHEMAS["companies.csv"]
    
    used_tax_ids = set()
    
    # Creación y escritura del CSV, generando cada fila con datos sintéticos realistas
    with output_file.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        for index in range(1, rows + 1):
            # Aplicamos un perfil latente LFR para sesgar atributos de empresa.
            profile = profiles[index - 1]
            if rng.random() > profile.mixing_mu and profile.anchor_province in cities_by_province:
                province_cities = cities_by_province[profile.anchor_province]
                province_weights = weights_by_province[profile.anchor_province]
                city_point = rng.choices(province_cities, weights=province_weights, k=1)[0]
            else:
                city_point = rng.choices(municipalities, weights=municipality_weights, k=1)[0]

            # El tamaño de la empresa se sesga el grado esperado del nodo en la red.
            size_band = _size_band_from_lfr(profile.degree_propensity, rng)
            
            # Generamos un ID de empresa único y un CIF (tax_id) asegurando la unicidad.
            company_id = f"COMP-{index:07d}"
            
            attempts = 0
            max_attempts = 50
            while attempts < max_attempts:
                cif_candidate = f"ES{fake.cif()}"
                if cif_candidate not in used_tax_ids:
                    used_tax_ids.add(cif_candidate)
                    break
                attempts += 1
            
            if attempts == max_attempts:
                cif_candidate = f"ESX{index:07d}"
                used_tax_ids.add(cif_candidate)
                logging.warning(f"Colisión probabilística máxima alcanzada para Tax ID en {company_id}. Usando fallback determinista.")
                
            record = {
                "company_id:ID(Company)": company_id,
                "legal_name:string": fake.company(),
                "tax_id:string": cif_candidate,
                "edi_endpoint:string": f"as2://edi.{company_id.lower()}.b2b.local/inbox",
                "node_role:string": _node_role_from_lfr(profile.degree_propensity, profile.mixing_mu, rng),
                "country:string": "ES",
                "region:string": city_point.province,
                "city:string": city_point.municipality,
                "latitude:float": round(city_point.lat + rng.uniform(-GEO_JITTER_DEG, GEO_JITTER_DEG), 6),
                "longitude:float": round(city_point.lon + rng.uniform(-GEO_JITTER_DEG, GEO_JITTER_DEG), 6),
                "industry_code:string": _industry_from_lfr(profile.preferred_industries, rng),
                "size_band:string": size_band,
                "baseline_revenue:float": _baseline_revenue(size_band, rng),
                "created_at:datetime": fake.date_time_between(start_date='-8y', end_date='now', tzinfo=timezone.utc).isoformat(),
                "is_active:boolean": rng.choices([True, False], weights=[0.95, 0.05], k=1)[0],
            }
            writer.writerow(record)
            
    logging.info(f"Escritura completada: {rows} entidades Company exportadas a {output_file.name}")
    return output_file


# =============================================================================
#  LÓGICA DE ALTO NIVEL (FUNCIONES AUXILIARES PARA SINTETIZAR EMPRESAS)
# =============================================================================
def load_municipalities(csv_path: Path) -> tuple[list[MunicipalityPoint], list[int]]:
    """Carga el dataset geográfico de municipios y sus pesos poblacionales.

    Args:
        csv_path: Ruta al CSV ``municipios_espana.csv``.

    Returns:
        Lista de municipios y sus pesos (población) para muestreo ponderado.

    Raises:
        ValueError: Si el CSV no contiene municipios válidos.
    """
    municipalities = []
    municipality_weights = []
    
    # Apertura del CSV con manejo de codificación y delimitador.
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            province = (row.get("Provincia") or "").strip()
            municipality = (row.get("Población") or "").strip()
            
            if not municipality or not province:
                continue
            
            pop = safe_int(row.get("Habitantes"), 50_000)
            
            mun = MunicipalityPoint(
                province=province,
                municipality=municipality,
                lat=safe_float(row.get("Latitud"), 0.0),
                lon=safe_float(row.get("Longitud"), 0.0),
                population=pop
            )
            
            municipalities.append(mun)
            municipality_weights.append(pop)
                
    if not municipalities:
        logging.error("Fallo estructural: El archivo de municipios base está vacío o corrupto.")
        raise ValueError("No se encontraron municipios válidos en el dataset proporcionado.")
        
    return municipalities, municipality_weights


def _build_lfr_profiles(rows: int, municipalities: list[MunicipalityPoint], municipality_weights: list[int], rng: random.Random,
                        gamma: float, beta: float, mu: float, min_comm: int, max_comm: int) -> list[LFRProfile]:
    """Construye perfiles LFR latentes para todas las empresas a sintetizar.

    Args:
        rows: Número total de empresas a generar.
        municipalities: Lista de municipios cargada desde ``municipios_espana.csv``.
        municipality_weights: Pesos poblacionales paralelos a ``municipalities``.
        rng: Generador aleatorio inicializado con la semilla global.
        gamma: Exponente de la distribución de grados (Pareto).
        beta: Exponente de la distribución de tamaños de comunidad (Pareto).
        mu: Coeficiente de mezcla LFR global (center de la Beta por nodo).
        min_comm: Tamaño mínimo de comunidad.
        max_comm: Tamaño máximo de comunidad.

    Returns:
        Lista de ``LFRProfile`` barajada aleatoriamente, una entrada por empresa.
    """
    community_sizes = _sample_community_sizes(beta, min_comm, max_comm, rows, rng)
    community_sizes.sort(reverse=True)
    most_populated_province = _get_most_populated_province(municipalities)
    
    profiles: list[LFRProfile] = []
    community_id = 1
    
    # Para cada comunidad, asignamos una provincia ancla y preferencia industrial.
    for idx, size in enumerate(community_sizes):
        if idx == 0:
            anchor_province = most_populated_province
        else:
            anchor_province = rng.choices(municipalities, weights=municipality_weights, k=1)[0].province
            
        preferred_size = min(3, len(INDUSTRY_CODES))
        preferred_industries = tuple(rng.sample(INDUSTRY_CODES, k=preferred_size))
        
        for _ in range(size):
            profiles.append(
                LFRProfile(
                    community_id=community_id,
                    anchor_province=anchor_province,
                    preferred_industries=preferred_industries,
                    degree_propensity=_sample_degree_propensity(gamma, rng),
                    mixing_mu=_sample_mixing_mu(mu, rng),
                )
            )
        community_id += 1
    
    # Mezclamos los perfiles para romper cualquier ordenamiento residual.
    rng.shuffle(profiles)
    return profiles


# =============================================================================
#  FUNCIONES AUXILIARES (Helpers / Utils)
# =============================================================================
def _size_band_from_lfr(degree_propensity: float, rng: random.Random) -> str:
    """Sesga la categoría de size_band según la jerarquía de grado del nodo en la red.

    Args:
        degree_propensity: Grado esperado del nodo, muestreado de una distribución Pareto.
        rng: Generador aleatorio inicializado con la semilla global.

    Returns:
        Una de las categorías de ``SIZE_BANDS``: ``micro``, ``pyme``, ``mid`` o ``enterprise``.
    """
    if degree_propensity >= 10: 
        weights = [0.10, 0.25, 0.40, 0.25] # Nodos con grado altos suelen ser medianas o grandes empresas.
    elif degree_propensity >= 4:
        weights = [0.25, 0.40, 0.25, 0.10] # Nodos con grado medio suelen ser pymes o medianas.
    else:
        weights = [0.55, 0.30, 0.12, 0.03] # Nodos con bajo grado suelen ser microempresas o pymes.
    return rng.choices(SIZE_BANDS, weights=weights, k=1)[0]


def _node_role_from_lfr(degree_propensity: float, mixing_mu: float, rng: random.Random) -> str:
    """Asigna el rol operativo (SUPPLIER, BUYER, HYBRID) sesgado por la importancia del nodo.

    Args:
        degree_propensity: Grado esperado del nodo; valores altos favorecen el rol ``HYBRID``.
        mixing_mu: Proporción de aristas inter-comunidad; valores altos favorecen ``BUYER``.
        rng: Generador aleatorio inicializado con la semilla global.

    Returns:
        Una de las cadenas de ``NODE_ROLES``: ``SUPPLIER``, ``BUYER`` o ``HYBRID``.
    """
    if degree_propensity >= 8: 
        weights = [0.10, 0.10, 0.80] # Nodos con alto grado tienden a ser hibridos.
    elif mixing_mu >= 0.5: 
        weights = [0.20, 0.40, 0.40] # Nodos con mu alto tienden a ser compradores o híbridos.
    else:
        weights = [0.25, 0.25, 0.50] # Nodos con mu bajo tienden a ser proveedores o híbridos.
        
    return rng.choices(NODE_ROLES, weights=weights, k=1)[0]


def _industry_from_lfr(preferred_industries: tuple[str, ...], rng: random.Random) -> str:
    """Asigna la industria haciendo que las preferidas del clúster sean 4 veces más probables.

    Args:
        preferred_industries: Códigos NACE preferidos por la comunidad LFR del nodo.
        rng: Generador aleatorio inicializado con la semilla global.

    Returns:
        Código NACE seleccionado (p. ej. ``C25``, ``G46``).
    """
    weights = [4.0 if code in preferred_industries else 1.0 for code in INDUSTRY_CODES]
    return rng.choices(INDUSTRY_CODES, weights=weights, k=1)[0]


def _baseline_revenue(size_band: str, rng: random.Random) -> float:
    """Asigna ingresos anuales (baseline_revenue) coherentes con el tamaño de la empresa.

    Args:
        size_band: Categoría de tamaño de la empresa (``micro``, ``pyme``, ``mid``, ``enterprise``).
        rng: Generador aleatorio inicializado con la semilla global.

    Returns:
        Importe anual de ingresos base (€), redondeado a dos decimales.
    """
    ranges = {
            "micro": (30_000, 600_000),
            "pyme": (600_000, 4_000_000),
            "mid": (4_000_000, 30_000_000),
            "enterprise": (30_000_000, 200_000_000),
    }
    low, high = ranges[size_band]
    return round(rng.uniform(low, high), 2)


def _sample_community_sizes(beta: float, min_comm: int, max_comm: int, rows: int, rng: random.Random) -> list[int]:
    """Genera tamaños de comunidad con distribución tipo power-law acotadas.

    Args:
        beta: Exponente de la distribución Pareto para tamaños de comunidad.
        min_comm: Tamaño mínimo permitido por comunidad.
        max_comm: Tamaño máximo permitido por comunidad.
        rows: Número total de empresas que deben quedar cubiertas.
        rng: Generador aleatorio inicializado con la semilla global.

    Returns:
        Lista de enteros que suman exactamente ``rows``, cada uno en ``[min_comm, max_comm]``.
    """
    sizes: list[int] = []
    total = 0
    while total < rows:
        sampled = int(rng.paretovariate(beta - 1.0) * min_comm)
        size = max(min_comm, min(sampled, max_comm))
        if total + size > rows:
            size = rows - total
        sizes.append(size)
        total += size
    return sizes


def _get_most_populated_province(municipalities: list[MunicipalityPoint]) -> str:
    """Calcula la provincia con mayor población agregada.

    Args:
        municipalities: Lista completa de municipios cargada desde el CSV geográfico.

    Returns:
        Nombre de la provincia con la suma de habitantes más alta.
    """
    pop_by_province = {}
    for mun in municipalities:
        pop_by_province[mun.province] = pop_by_province.get(mun.province, 0) + mun.population
    
    # Devuelve el nombre de la provincia con la suma total más alta
    return max(pop_by_province.items(), key=lambda x: x[1])[0]


def _sample_degree_propensity(gamma: float, rng: random.Random) -> float:
    """Calcula el grado esperado del nodo usando una distribución Pareto parametrizada por ``gamma``.

    Args:
        gamma: Exponente de la distribución de grados LFR. Debe ser ``> 1.0``.
        rng: Generador aleatorio inicializado con la semilla global.

    Returns:
        Grado esperado acotado en el rango ``[1.0, 30.0]``.
    """
    alpha = max(gamma - 1.0, 1.05)
    # Distribución de pareto para sesgar hacia nodos con bajo grado
    return max(1.0, min(rng.paretovariate(alpha), 30.0)) 
    # Visualizacion aqui: https://www.wolframalpha.com/input?i=PDF+of+ParetoDistribution%5B1%2C+1.4%5D+from+1+to+10&lang=es


def _sample_mixing_mu(mu: float, rng: random.Random) -> float:
    """Genera la mezcla de comunidades alrededor del ``mu`` global usando una distribución Beta.

    Args:
        mu: Coeficiente de mezcla LFR global; actúa como media de la distribución Beta.
        rng: Generador aleatorio inicializado con la semilla global.

    Returns:
        Valor de mezcla por nodo acotado en ``[0.05, 0.95]``, redondeado a 3 decimales.
    """
    concentration = 18.0
    a = max(mu * concentration, 0.1)
    b = max((1.0 - mu) * concentration, 0.1)
    # Distribución beta para sesgar con varianza controlada alrededor de LFR_MIXING_MU
    return round(max(0.05, min(rng.betavariate(a, b), 0.95)), 3)
    # Visualizacion aqui: https://www.wolframalpha.com/input?i=PDF+of+BetaDistribution%5B5.4%2C+12.6%5D+from+0+to+1&lang=es
