"""Sintetizador de productos correlacionados con proveedores e industria.

Genera ``products.csv`` asignando a cada proveedor un catálogo de productos
proporcional a su peso en la red (``baseline_revenue``, ``out_degree``,
``agreed_volume_total``).  La categoría de cada producto se elige según
probabilidades previas por código NACE definidas en ``INDUSTRY_CATEGORY_PRIORS``.
"""
from __future__ import annotations

import argparse
import csv
import math
import random
from dataclasses import dataclass
from pathlib import Path
from backend.etl.generation.csv_templates import CSV_SCHEMAS
from backend.core.utils import safe_float

# =============================================================================
# CABECERA (Configuracion y catalogo)
# =============================================================================
PRODUCT_CATEGORIES: dict[str, dict[str, object]] = {
    "raw_materials": {
        "label": "Raw Materials",
        "unit": "kg",
        "hs_prefixes": ["10", "12", "15", "28", "29", "31", "39", "72", "76"],
        "criticality_weights": [0.20, 0.55, 0.25],
        "substitutable_prob": 0.60,
        "lead_time_range": (2, 12),
        "lead_time_variance": 0.22,
        "price_range": (0.50, 150.00),
        "price_volatility": 0.32,
        "nouns": ["Granulate", "Resin", "Composite", "Alloy", "Powder", "Ingot", "Coil", "Sheet", "Pellet", "Catalyst", "Solvent", "Fiber"],
    },
    "components": {
        "label": "Components",
        "unit": "unit",
        "hs_prefixes": ["73", "84", "85", "87", "90"],
        "criticality_weights": [0.12, 0.58, 0.30],
        "substitutable_prob": 0.48,
        "lead_time_range": (4, 18),
                "lead_time_variance": 0.18,
        "price_range": (2.50, 250.00),
                "price_volatility": 0.18,
        "nouns": ["Valve", "Actuator", "Sensor", "Connector", "Bearing", "Controller", "Module", "Inverter", "PLC", "Encoder", "Nozzle", "Manifold"],
    },
    "packaging": {
        "label": "Packaging",
        "unit": "unit",
        "hs_prefixes": ["39", "48", "73", "76"],
        "criticality_weights": [0.50, 0.40, 0.10],
        "substitutable_prob": 0.72,
        "lead_time_range": (1, 7),
                "lead_time_variance": 0.10,
        "price_range": (0.05, 12.00),
                "price_volatility": 0.10,
        "nouns": ["Pallet", "Box", "Container", "Sleeve", "Cap", "Wrap", "Drum", "IBC", "Crate", "Label Roll", "Foam Insert", "Strap"],
    },
    "spare_parts": {
        "label": "Spare Parts",
        "unit": "unit",
        "hs_prefixes": ["84", "85", "87", "90"],
        "criticality_weights": [0.10, 0.45, 0.45],
        "substitutable_prob": 0.35,
        "lead_time_range": (3, 21),
                "lead_time_variance": 0.27,
        "price_range": (4.00, 480.00),
                "price_volatility": 0.22,
        "nouns": ["Rotor", "Pump", "Relay", "Transmitter", "Seal", "Gear", "Filter", "Impeller", "Gasket", "Cartridge", "Fuse", "Drive Belt"],
    },
    "critical_equipment": {
        "label": "Critical Equipment",
        "unit": "unit",
        "hs_prefixes": ["84", "85"],
        "criticality_weights": [0.05, 0.15, 0.80],
        "substitutable_prob": 0.05, 
        "lead_time_range": (2, 7),
        "lead_time_variance": 0.10,
        "price_range": (5000.00, 500000.00),
        "price_volatility": 0.28,
        "nouns": ["Reactor", "Turbine", "Server Rack", "CNC Machine", "Conveyor System", "Boiler", "Heat Exchanger", "Compressor", "Furnace", "Chiller"],
    },
    "logistics_services": { 
        "label": "Logistics Services",
        "units": ["km", "pallet/day", "container", "flat_fee"],
        "hs_prefixes": ["99"],
        "criticality_weights": [0.10, 0.40, 0.50],
        "substitutable_prob": 0.50,
        "lead_time_range": (0, 5),
        "lead_time_variance": 0.20,
        "price_range": (50.00, 2500.00),
        "price_volatility": 0.20,
        "nouns": ["Freight", "Warehousing", "Last-Mile", "Customs Clearance", "Distribution", "Cross-Docking", "Cold Chain", "Linehaul"],
    },
    "professional_services": {
        "label": "Professional Services",
        "unit": "hour",
        "hs_prefixes": ["99"],
        "criticality_weights": [0.40, 0.45, 0.15],
        "substitutable_prob": 0.25,
        "lead_time_range": (0, 14),
        "lead_time_variance": 0.15,
        "price_range": (40.00, 300.00),
        "price_volatility": 0.14,
        "nouns": ["Calibration", "Audit", "Maintenance", "Integration", "Support", "Training", "Validation", "Retrofit", "Cybersecurity Audit", "SLA Support"],
    },
}

INDUSTRY_CATEGORY_PRIORS: dict[str, dict[str, float]] = {
    "C10": {"raw_materials": 0.42, "components": 0.18, "packaging": 0.25, "spare_parts": 0.07, "critical_equipment": 0.04, "logistics_services": 0.02, "professional_services": 0.02},
    "C13": {"raw_materials": 0.39, "components": 0.20, "packaging": 0.24, "spare_parts": 0.09, "critical_equipment": 0.03, "logistics_services": 0.03, "professional_services": 0.02},
    "C20": {"raw_materials": 0.43, "components": 0.21, "packaging": 0.14, "spare_parts": 0.10, "critical_equipment": 0.06, "logistics_services": 0.03, "professional_services": 0.03},
    "C22": {"raw_materials": 0.33, "components": 0.26, "packaging": 0.21, "spare_parts": 0.10, "critical_equipment": 0.04, "logistics_services": 0.03, "professional_services": 0.03},
    "C25": {"raw_materials": 0.16, "components": 0.39, "packaging": 0.07, "spare_parts": 0.24, "critical_equipment": 0.08, "logistics_services": 0.03, "professional_services": 0.03},
    "C26": {"raw_materials": 0.08, "components": 0.39, "packaging": 0.05, "spare_parts": 0.21, "critical_equipment": 0.12, "logistics_services": 0.05, "professional_services": 0.10},
    "C28": {"raw_materials": 0.12, "components": 0.36, "packaging": 0.05, "spare_parts": 0.25, "critical_equipment": 0.12, "logistics_services": 0.04, "professional_services": 0.06},
    "C29": {"raw_materials": 0.11, "components": 0.39, "packaging": 0.05, "spare_parts": 0.24, "critical_equipment": 0.12, "logistics_services": 0.04, "professional_services": 0.05},
    "G46": {"raw_materials": 0.18, "components": 0.22, "packaging": 0.31, "spare_parts": 0.12, "critical_equipment": 0.04, "logistics_services": 0.08, "professional_services": 0.05},
    "H52": {"raw_materials": 0.05, "components": 0.05, "packaging": 0.15, "spare_parts": 0.05, "critical_equipment": 0.05, "logistics_services": 0.55, "professional_services": 0.10},
    "J62": {"raw_materials": 0.01, "components": 0.08, "packaging": 0.01, "spare_parts": 0.07, "critical_equipment": 0.18, "logistics_services": 0.10, "professional_services": 0.55},
    "M71": {"raw_materials": 0.03, "components": 0.14, "packaging": 0.03, "spare_parts": 0.10, "critical_equipment": 0.24, "logistics_services": 0.08, "professional_services": 0.38},
}

ADJECTIVES = [
    "Standard", "Industrial", "Precision", "Certified", 
    "Modular", "HighDensity", "Eco", "Advanced", "Custom", 
    "Premium","Heavy-Duty", "Outsourced", "Automated"
]

CRITICALITY_LEVELS = ["LOW", "MEDIUM", "HIGH"]


def _pick(row: dict[str, str], *keys: str) -> str | None:
    """Devuelve el primer valor no nulo encontrado en el dict para las claves dadas.

    Args:
        row: Fila del CSV como diccionario ``{header: value}``.
        *keys: Claves a probar en orden de prioridad.

    Returns:
        Valor de la primera clave encontrada, o ``None`` si ninguna existe.
    """
    for key in keys:
        if key in row and row[key] is not None:
            return row[key]
    return None

@dataclass(frozen=True)
class SupplierProfile:
    """Perfil de proveedor enriquecido con métricas de red para la síntesis de productos.

    Attributes:
        company_id: Identificador único del proveedor.
        industry_code: Código NACE de la industria.
        baseline_revenue: Ingresos anuales base en euros.
        out_degree: Número de compradores a los que suministra (aristas salientes).
        agreed_volume_total: Volumen contractual total acordado en euros.
    """

    company_id: str
    industry_code: str
    baseline_revenue: float
    out_degree: int
    agreed_volume_total: float


# =============================================================================
# INTERFAZ PUBLICA (CLI)
# =============================================================================
def get_products_parser() -> argparse.ArgumentParser:
    """Contiene solo los argumentos exclusivos de este modulo."""
    parser = argparse.ArgumentParser(add_help=False)
    group = parser.add_argument_group("Opciones de products.csv")
    group.add_argument("--avg-degree-products", type=int, default=25, help="Multiplicador de frecuencia de productos por pedido", metavar="N",)
    return parser


# =============================================================================
# FUNCION PRINCIPAL (MAIN)
# =============================================================================
def synthesize_products_csv(output_file: Path, companies_csv: Path, rel_supplies_csv: Path,
                            avg_degree_products: int, seed: int) -> Path:
    """Genera products.csv correlacionando el catálogo con proveedores e industria.

    El número total de productos es ``len(suppliers) × avg_degree_products``.
    La categoría de cada producto se elige según ``INDUSTRY_CATEGORY_PRIORS``.

    Args:
        output_file: Ruta del fichero CSV de salida.
        companies_csv: Ruta al CSV de empresas generado previamente.
        rel_supplies_csv: Ruta al CSV de suministros generado previamente.
        avg_degree_products: Número medio de productos por proveedor.
        seed: Semilla para reproducibilidad.

    Returns:
        Ruta al fichero CSV escrito.

    Raises:
        ValueError: Si ``avg_degree_products <= 0`` o no hay proveedores válidos.
        FileNotFoundError: Si ``companies_csv`` o ``rel_supplies_csv`` no existen.
    """
    if avg_degree_products <= 0:
        raise ValueError("avg-degree-products debe ser > 0")

    rng = random.Random(seed)
    output_file.parent.mkdir(parents=True, exist_ok=True)
 
    # Carga de datos de los supplier
    suppliers = _load_supplier_profiles(companies_csv, rel_supplies_csv, rng)
 
    if not suppliers:
        raise ValueError("No se han encontrado proveedores validos para sintetizar productos")

    # Numero de productos a generar basado en el numero de proveedores y argumento (avg-degree-products)
    rows = max(len(suppliers) * avg_degree_products, 1)

    fieldnames = CSV_SCHEMAS["products.csv"]

    # Calculo de pesos para seleccion de proveedores y categorias
    used_skus: set[str] = set()
    supplier_weights = [_supplier_weight(s) for s in suppliers]
    product_suppliers = suppliers[:]
    rng.shuffle(product_suppliers)

    if rows > len(product_suppliers):
        product_suppliers.extend(
            rng.choices(suppliers, weights=supplier_weights, k=rows - len(product_suppliers))
        )
    else:
        product_suppliers = product_suppliers[:rows]

    with output_file.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        for idx, supplier in enumerate(product_suppliers, start=1):
            # Selecciona un proveedor ponderado por su perfil y calcula atributos del producto correlacionados a su industria
            industry_code = supplier.industry_code
            category_key = _choose_category_by_industry(industry_code, rng)
            category_cfg = PRODUCT_CATEGORIES[category_key]
            
            #Calculo de atributos del producto
            sku = _generate_unique_sku(category_key, industry_code, rng, used_skus)
            hs_code = _generate_hs_code(category_cfg, industry_code, rng)
            name = _generate_name(category_cfg, industry_code, hs_code, rng)
            unit = _pick_unit(category_cfg, rng)
            criticality = rng.choices(CRITICALITY_LEVELS, weights=category_cfg["criticality_weights"],k=1,)[0]
            base_price = _price_for_category(category_cfg, criticality, rng)
            lead_time = _lead_time_from_criticality(category_cfg, criticality, rng)
            substitutable = _is_substitutable(category_cfg, criticality, rng)

            writer.writerow(
                {
                    "product_id:ID(Product)": f"PROD-{idx:07d}",
                    "sku:string": sku,
                    "hs_code:string": hs_code,
                    "name:string": name,
                    "category:string": category_cfg["label"],
                    "unit:string": unit,
                    "base_price:float": base_price,
                    "lead_time_baseline_days:int": lead_time,
                    "criticality:string": criticality,
                    "is_substitutable:boolean": substitutable,
                    "supplier_company_id:string": supplier.company_id,
                }
            )

    return output_file


# =============================================================================
# FUNCIONES AUXILIARES (Helpers / Utils)
# =============================================================================
def _load_supplier_profiles(companies_csv: Path, rel_supplies_csv: Path, rng: random.Random) -> list[SupplierProfile]:
    """Carga y correlaciona datos de companies.csv y rel_supplies.csv para construir perfiles de proveedores.

    Args:
        companies_csv: Ruta al CSV de empresas generado por ``synthesize_companies_csv``.
        rel_supplies_csv: Ruta al CSV de suministros generado por ``synthesize_rel_supplies_csv``.
        rng: Generador aleatorio inicializado con la semilla global (reservado para extensiones futuras).

    Returns:
        Lista de ``SupplierProfile`` con grado de salida y volumen acordado agregados desde SUPPLIES.

    Raises:
        FileNotFoundError: Si alguno de los dos CSV no existe.
    """
    if not companies_csv.exists():
        raise FileNotFoundError(f"No existe companies.csv: {companies_csv}")
    if not rel_supplies_csv.exists():
        raise FileNotFoundError(f"No existe rel_supplies.csv: {rel_supplies_csv}")

    # Dicionario temporal para almacenar datos de empresas
    companies: dict[str, tuple[str, float]] = {} # company_id -> (industry_code, baseline_revenue)
    
    with companies_csv.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            company_id = (_pick(row, "company_id:ID(Company)", "company_id") or "").strip()
            if not company_id:
                continue
            
            industry_code = (_pick(row, "industry_code:string", "industry_code") or "").strip().upper()
            baseline_revenue = max(safe_float(_pick(row, "baseline_revenue:float", "baseline_revenue"), 30_000.0), 30_000.0)
            companies[company_id] = (industry_code, baseline_revenue)

    stats: dict[str, dict[str, float]] = {} # supplier_company_id -> {out_degree, agreed_volume}
    
    with rel_supplies_csv.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            supplier_company_id = (_pick(row, ":START_ID(Company)", "supplier_company_id") or "").strip()
            if not supplier_company_id or supplier_company_id not in companies:
                continue
            bucket = stats.setdefault(supplier_company_id, {"out_degree": 0.0, "agreed_volume": 0.0})
            bucket["out_degree"] += 1.0
            bucket["agreed_volume"] += max(safe_float(_pick(row, "agreed_volume_baseline:float", "agreed_volume_baseline"), 0.0), 0.0)

    suppliers: list[SupplierProfile] = []
    for supplier_company_id, values in stats.items():
        industry_code, baseline_revenue = companies[supplier_company_id]
        suppliers.append(
            SupplierProfile(
                company_id=supplier_company_id,
                industry_code=industry_code,
                baseline_revenue=baseline_revenue,
                out_degree=int(values["out_degree"]),
                agreed_volume_total=values["agreed_volume"],
            )
        )

    return suppliers


def _supplier_weight(supplier: SupplierProfile) -> float:
    """Calcula un peso de selección de proveedores basado en revenue, conexiones y volumen acordado.

    Args:
        supplier: Perfil del proveedor con métricas de red enriquecidas.

    Returns:
        Peso positivo para muestreo ponderado; mínimo 1.0.
    """
    return max(
        (math.sqrt(supplier.baseline_revenue) * 0.35)
        + ((supplier.out_degree + 1) ** 1.10)
        + (math.log1p(supplier.agreed_volume_total) * 0.75),
        1.0,
    )


def _choose_category_by_industry(industry_code: str, rng: random.Random) -> str:
    """Selecciona una categoría de producto basada en el código de industria del proveedor.

    Args:
        industry_code: Código NACE del proveedor (p. ej. ``C25``, ``G46``).
        rng: Generador aleatorio inicializado con la semilla global.

    Returns:
        Clave de categoría de ``PRODUCT_CATEGORIES`` (p. ej. ``components``, ``packaging``).
    """
    priors = INDUSTRY_CATEGORY_PRIORS.get(industry_code) or INDUSTRY_CATEGORY_PRIORS["G46"]
    categories = list(priors.keys())
    weights = list(priors.values())
    return rng.choices(categories, weights=weights, k=1)[0]


def _generate_unique_sku(category_key: str, industry_code: str, rng: random.Random, used_skus: set[str]) -> str:
    """Genera un SKU único combinando prefijos de categoría e industria con números aleatorios.

    Args:
        category_key: Clave de categoría (p. ej. ``components``).
        industry_code: Código NACE del proveedor (p. ej. ``C25``).
        rng: Generador aleatorio inicializado con la semilla global.
        used_skus: Conjunto de SKUs ya asignados en esta ejecución; se actualiza en el lugar.

    Returns:
        Cadena SKU única con formato ``{industry_prefix}{category_prefix}-{NNNN}-{NN}``.
    """
    prefix = f"{industry_code[:2]}{category_key[:2]}".upper()
    for _ in range(100):
        candidate = f"{prefix}-{rng.randint(1000, 9999)}-{rng.randint(10, 99)}"
        if candidate not in used_skus:
            used_skus.add(candidate)
            return candidate

    # Fallback defensivo si hay colisiones repetidas
    forced = f"{prefix}-{len(used_skus) + 1:06d}"
    used_skus.add(forced)
    return forced


def _generate_hs_code(category_cfg: dict[str, object], industry_code: str, rng: random.Random) -> str:
    """Genera un código HS aleatorio basado en los prefijos asociados a la categoría del producto.

    Args:
        category_cfg: Configuración de la categoría desde ``PRODUCT_CATEGORIES``.
        industry_code: Código NACE del proveedor, estabiliza el pool de sufijos con su propio RNG.
        rng: Generador aleatorio inicializado con la semilla global.

    Returns:
        Código HS de 6 dígitos como cadena (p. ej. ``847523``).
    """
    hs_prefix = rng.choice(category_cfg["hs_prefixes"])
    pool_rng = random.Random(f"{hs_prefix}_{industry_code}_v1")
    
    valid_suffixes = [
        f"{pool_rng.randint(1, 90):02d}{pool_rng.randint(1, 90):02d}" 
        for _ in range(5)
    ]

    suffix = rng.choices(valid_suffixes, weights=[0.40, 0.25, 0.20, 0.10, 0.05], k=1)[0]
    
    return f"{hs_prefix}{suffix}"


def _generate_name(category_cfg: dict[str, object], industry_code: str, hs_code: str, rng: random.Random) -> str:
    """Genera un nombre de producto combinando adjetivo, sustantivo de categoría y códigos de industria.

    Args:
        category_cfg: Configuración de la categoría desde ``PRODUCT_CATEGORIES``.
        industry_code: Código NACE del proveedor (incluido como prefijo en el nombre).
        hs_code: Código HS asignado al producto; los dos últimos dígitos forman la familia.
        rng: Generador aleatorio inicializado con la semilla global.

    Returns:
        Nombre del producto como cadena (p. ej. ``"Precision Valve C25-23"``).
    """
    adjective = rng.choice(ADJECTIVES)
    noun = rng.choice(category_cfg["nouns"])
    family = hs_code[-2:] if hs_code and len(hs_code) >= 2 else f"{rng.randint(10, 99):02d}"
    
    return f"{adjective} {noun} {industry_code}-{family}"


def _pick_unit(category_cfg: dict[str, object], rng: random.Random) -> str:
    """Selecciona la unidad de medida del producto de la lista disponible en la categoría.

    Args:
        category_cfg: Configuración de la categoría desde ``PRODUCT_CATEGORIES``.
        rng: Generador aleatorio inicializado con la semilla global.

    Returns:
        Cadena de unidad (p. ej. ``"kg"``, ``"unit"``, ``"hour"``).
    """
    units = category_cfg.get("units")
    if isinstance(units, list) and units:
        return str(rng.choice(units))
    return str(category_cfg.get("unit", "unit"))


def _lead_time_from_criticality(category_cfg: dict[str, object], criticality: str, rng: random.Random) -> int:
    """Calcula el tiempo de entrega base en días según categoría y criticidad del producto.

    Args:
        category_cfg: Configuración de la categoría desde ``PRODUCT_CATEGORIES``.
        criticality: Nivel de criticidad del producto (``LOW``, ``MEDIUM`` o ``HIGH``).
        rng: Generador aleatorio inicializado con la semilla global.

    Returns:
        Número entero de días de lead time, mínimo 0.
    """
    min_days, max_days = category_cfg["lead_time_range"]
    base = rng.randint(min_days, max_days)
    variance = float(category_cfg.get("lead_time_variance", 0.0))

    if criticality == "HIGH":
        base = int(round(base * 1.25))
        variance *= 1.25
    elif criticality == "LOW":
        base = int(round(base * 0.85))
        variance *= 0.85

    if variance > 0.0:
        noise = rng.gauss(0.0, variance)
        base = int(round(base * max(0.1, (1.0 + noise))))

    return max(base, 0)


def _price_for_category(category_cfg: dict[str, object], criticality: str, rng: random.Random) -> float:
    """Calcula el precio base del producto según categoría y criticidad, con ruido de volatilidad.

    Args:
        category_cfg: Configuración de la categoría desde ``PRODUCT_CATEGORIES``.
        criticality: Nivel de criticidad del producto (``LOW``, ``MEDIUM`` o ``HIGH``).
        rng: Generador aleatorio inicializado con la semilla global.

    Returns:
        Precio base en euros, redondeado a 2 decimales, mínimo 0.01.
    """
    low, high = category_cfg["price_range"]
    price = rng.uniform(low, high)
    volatility = float(category_cfg.get("price_volatility", 0.0))

    if criticality == "HIGH":
        price *= rng.uniform(1.10, 1.35)
        volatility *= 1.20
    elif criticality == "LOW":
        price *= rng.uniform(0.88, 0.98)
        volatility *= 0.85

    if volatility > 0.0:
        price *= (1.0 + rng.uniform(-volatility, volatility))

    return round(max(price, 0.01), 2)


def _is_substitutable(category_cfg: dict[str, object], criticality: str, rng: random.Random) -> bool:
    """Determina si un producto es sustituible según la probabilidad base de su categoría y criticidad.

    Args:
        category_cfg: Configuración de la categoría desde ``PRODUCT_CATEGORIES``.
        criticality: Nivel de criticidad del producto (``LOW``, ``MEDIUM`` o ``HIGH``);
            ``HIGH`` reduce la probabilidad de sustitución un 30 %.
        rng: Generador aleatorio inicializado con la semilla global.

    Returns:
        ``True`` si el producto puede ser reemplazado por otro equivalente.
    """
    base_prob = float(category_cfg["substitutable_prob"])
    if criticality == "HIGH":
        base_prob *= 0.70
    elif criticality == "LOW":
        base_prob *= 1.10
    return rng.random() < min(max(base_prob, 0.0), 1.0)

