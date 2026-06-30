"""Sintetizador de documentos EDI con historial temporal y trazabilidad.

Genera ``documents.csv`` en modo streaming (O(1) memoria): para cada par
proveedor-comprador del grafo emite triplets de documentos
(ORDER → DESADV → INVOICE) distribuidos a lo largo del periodo de actividad
del contrato con sesgo estacional mensual definido en ``MONTH_WEIGHTS``.
"""
from __future__ import annotations

import argparse
import csv
import logging
import random
from collections.abc import Generator
from dataclasses import dataclass
from datetime import date, datetime, timedelta, UTC
from pathlib import Path
from backend.etl.generation.csv_templates import CSV_SCHEMAS
from backend.core.utils import safe_float, safe_int, safe_date, pick

# =============================================================================
#  CABECERA (Configuración y Modelos)
# =============================================================================
SIMULATION_TODAY = date(2026, 1, 1)     # Reemplaza con date.today() en producción
EDI_STANDARDS = ["EDIFACT", "ANSI_X12"]

MONTH_WEIGHTS: dict[int, float] = {
    1: 0.85, 2: 0.85, 3: 0.95, 4: 1.00, 5: 1.05, 6: 1.20,
    7: 1.25, 8: 1.10, 9: 1.00, 10: 1.05, 11: 1.20, 12: 1.40,
}
MAX_MONTH_WEIGHT = max(MONTH_WEIGHTS.values())

INDUSTRY_TAX_RATES: dict[str, list[float]] = {
    "C10": [0.04, 0.10], "C13": [0.21], "C20": [0.21], "C22": [0.21],
    "C25": [0.21], "C26": [0.21], "C28": [0.21], "C29": [0.21],
    "G46": [0.10, 0.21], "H52": [0.21], "J62": [0.21], "M71": [0.21],
}

@dataclass(frozen=True)
class CompanyProfile:
    """Perfil mínimo de empresa necesario para la síntesis de documentos.

    Attributes:
        company_id: Identificador único de la empresa.
        country: Código del país.
        industry_code: Código NACE (determina el tipo de IVA aplicable).
        baseline_revenue: Ingresos anuales base en euros.
    """

    company_id: str
    country: str
    industry_code: str
    baseline_revenue: float


@dataclass(frozen=True)
class CompanyPair:
    """Contrato de suministro entre un proveedor y un comprador.

    Attributes:
        supplier_company_id: ID del proveedor.
        buyer_company_id: ID del comprador.
        lead_time_days: Plazo de entrega acordado en días.
        reliability_score: Fiabilidad del proveedor entre [0, 1].
        agreed_volume_baseline: Volumen contractual anual en euros.
        contract_type: Tipo de contrato: ``FRAME``, ``SPOT``, ``ANNUAL`` o ``MULTIYEAR``.
        payment_terms_days: Días de pago acordados.
        since_date: Fecha de inicio de la relación comercial.
    """

    supplier_company_id: str
    buyer_company_id: str
    lead_time_days: int
    reliability_score: float
    agreed_volume_baseline: float
    contract_type: str
    payment_terms_days: int
    since_date: date


# =============================================================================
#  INTERFAZ PÚBLICA (CLI)
# =============================================================================
def get_documents_parser() -> argparse.ArgumentParser:
    """Contiene solo los argumentos exclusivos de este módulo."""
    parser = argparse.ArgumentParser(add_help=False)
    group = parser.add_argument_group("Opciones de documents.csv")
    group.add_argument("--avg-degree-documents", type=int, default=5, help="Multiplicador de frecuencia de pedidos por contrato", metavar="N")
    return parser


# =============================================================================
#  FUNCIÓN ORQUESTADORA (MAIN)
# =============================================================================
def synthesize_documents_csv(output_file: Path, companies_csv: Path, rel_supplies_csv: Path,
                             seed: int, avg_out_degree: int) -> Path:
    """Genera documents.csv en modo streaming, emitiendo las tripletas ORDER→DESADV→INVOICE.

    Para cada par proveedor-comprador distribuye documentos a lo largo del
    periodo de actividad del contrato con sesgo estacional mensual
    (``MONTH_WEIGHTS``).  El generador ``_document_stream_generator`` asegura
    uso de memoria O(1) independientemente del tamaño del grafo.

    Args:
        output_file: Ruta del fichero CSV de salida.
        companies_csv: Ruta al CSV de empresas generado previamente.
        rel_supplies_csv: Ruta al CSV de suministros generado previamente.
        seed: Semilla para reproducibilidad.
        avg_out_degree: Multiplicador de frecuencia de pedidos por contrato.

    Returns:
        Ruta al fichero CSV escrito.

    Raises:
        ValueError: Si ``avg_out_degree <= 0`` o no hay pares en rel_supplies.csv.
    """
    if avg_out_degree <= 0:
        raise ValueError("avg_out_degree debe ser > 0")

    rng = random.Random(seed)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Carga de contextos
    company_profiles = _load_company_profiles(companies_csv)
    pairs = _load_pairs_from_supplies(rel_supplies_csv)
    if not pairs:
        raise ValueError("No hay relaciones en rel_supplies.csv para sintetizar documents.csv")

    fieldnames = CSV_SCHEMAS["documents.csv"]

    docs_generated = 0

    # Apertura del archivo en modo escritura y consumo del generador
    with output_file.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        
        # Pedimos los documentos de uno en uno al generador y los escribimos
        for record in _document_stream_generator(pairs, company_profiles, rng, avg_out_degree):
            writer.writerow(record)
            docs_generated += 1

    # Control final
    if docs_generated == 0:
        logging.warning("No se han generado documentos, revisa since_date en rel_supplies.csv")
    else:
        # Opcional: Un log para que veas en consola cuántos se generaron
        logging.info(f"Éxito: Se han generado {docs_generated} documentos en modo streaming.")

    return output_file


# =============================================================================
#  LÓGICA DE ALTO NIVEL (Cargas y Generadores Complejos)
# =============================================================================
def _load_company_profiles(companies_csv: Path) -> dict[str, CompanyProfile]:
    """Carga los perfiles mínimos de empresa necesarios para la síntesis de documentos.

    Args:
        companies_csv: Ruta al CSV de empresas generado por ``synthesize_companies_csv``.

    Returns:
        Diccionario ``{company_id: CompanyProfile}`` con los perfiles de todas las empresas.

    Raises:
        FileNotFoundError: Si ``companies_csv`` no existe.
    """
    if not companies_csv.exists():
        raise FileNotFoundError(f"No existe companies.csv: {companies_csv}")

    profiles: dict[str, CompanyProfile] = {}
    with companies_csv.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            company_id = (pick(row, "company_id:ID(Company)", "company_id") or "").strip()
            if not company_id:
                continue
            profiles[company_id] = CompanyProfile(
                company_id=company_id,
                country=(pick(row, "country:string", "country") or "ES").strip().upper(),
                industry_code=(pick(row, "industry_code:string", "industry_code") or "G46").strip().upper(),
                baseline_revenue=max(safe_float(pick(row, "baseline_revenue:float", "baseline_revenue"), 30_000.0), 30_000.0),
            )
    return profiles


def _load_pairs_from_supplies(rel_supplies_csv: Path) -> list[CompanyPair]:
    """Carga los contratos proveedor-comprador desde rel_supplies.csv.

    Args:
        rel_supplies_csv: Ruta al CSV de suministros generado por ``synthesize_rel_supplies_csv``.

    Returns:
        Lista de ``CompanyPair`` con los datos contractuales de cada relación SUPPLIES.
        Devuelve lista vacía si el fichero no existe.
    """
    if not rel_supplies_csv.exists():
        return []

    pairs: list[CompanyPair] = []
    fallback_since = SIMULATION_TODAY - timedelta(days=365)
    with rel_supplies_csv.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            supplier = (pick(row, ":START_ID(Company)", "supplier_company_id") or "").strip()
            buyer = (pick(row, ":END_ID(Company)", "buyer_company_id") or "").strip()
            if not supplier or not buyer or supplier == buyer:
                continue
            pairs.append(
                CompanyPair(
                    supplier_company_id=supplier,
                    buyer_company_id=buyer,
                    lead_time_days=max(safe_int(pick(row, "lead_time_days:int", "lead_time_days"), 2), 0),
                    reliability_score=min(max(safe_float(pick(row, "reliability_score:float", "reliability_score"), 0.9), 0.0), 1.0),
                    agreed_volume_baseline=max(safe_float(pick(row, "agreed_volume_baseline:float", "agreed_volume_baseline"), 1_000.0), 100.0),
                    contract_type=(pick(row, "contract_type:string", "contract_type") or "FRAME").strip().upper(),
                    payment_terms_days=max(safe_int(pick(row, "payment_terms_agreed:int", "payment_terms_agreed"), 30), 0),
                    since_date=safe_date(pick(row, "since_date:datetime", "since_date"), fallback_since),
                )
            )
    return pairs


def _document_stream_generator(pairs: list[CompanyPair], company_profiles: dict[str, CompanyProfile],
                               rng: random.Random, avg_out_degree: int) -> Generator[dict, None, None]:
    """Generador que emite filas de documento B2B de una en una (streaming).

    Para cada par distribuye los pedidos en el tiempo con sesgo estacional
    y emite las filas como dicts listos para ``csv.DictWriter``.

    Args:
        pairs: Lista de contratos proveedor-comprador.
        company_profiles: Perfiles de empresa indexados por ``company_id``.
        rng: Generador de números aleatorios con semilla.
        avg_out_degree: Multiplicador de frecuencia de pedidos por contrato.

    Yields:
        dict: Fila de documento lista para escribir en ``documents.csv``.
    """
    next_seq = 1

    for pair in pairs:
        
        if pair.since_date > SIMULATION_TODAY:
            continue
        
        supplier_profile = company_profiles.get(pair.supplier_company_id)
        buyer_profile = company_profiles.get(pair.buyer_company_id)
        
        if supplier_profile is None or buyer_profile is None:
            continue

        active_start = min(pair.since_date, SIMULATION_TODAY)
        active_days = max((SIMULATION_TODAY - active_start).days, 1)
        active_years = active_days / 365.0
        
        total_historical_volume = max(pair.agreed_volume_baseline * active_years, 50.0)

        annual_orders = _determine_order_frequency(pair.contract_type, rng)
        scaled_annual_orders = _apply_frequency_scale(annual_orders, avg_out_degree)
        total_orders = max(1, int(round(scaled_annual_orders * active_years)))

        order_dates = _distribute_dates_with_seasonality(active_start, SIMULATION_TODAY, total_orders, rng)
        order_amounts = _distribute_volume(total_historical_volume, total_orders, rng)

        for order_date, order_gross in zip(order_dates, order_amounts):
            triplet_records = _generate_triplet_records(
                base_seq=next_seq, rng=rng, pair=pair,
                supplier_profile=supplier_profile, buyer_profile=buyer_profile,
                order_issue=order_date, order_gross=order_gross,
            )
            
            for doc in triplet_records:
                yield doc
                
            next_seq += 3


def _generate_triplet_records(base_seq: int, rng: random.Random, pair: CompanyPair,
                              supplier_profile: CompanyProfile, buyer_profile: CompanyProfile,
                              order_issue: date, order_gross: float) -> list[dict]:
    """Genera la tripleta EDI de un ciclo comercial: ORDER → DESADV → INVOICE.

    Los tres documentos comparten divisa, par proveedor-comprador y condiciones
    contractuales. La cadena de trazabilidad se construye así:

    - ``DESADV.reference_id = ORDER_ID``  →  DESADV → FULFILLS → ORDER (1 salto)
    - ``INVOICE.reference_id = DESADV_ID`` →  INVOICE → FULFILLS → DESADV → FULFILLS → ORDER (2 saltos)

    Los importes siguen la jerarquía ``delivery_gross = order_gross × fulfillment_ratio``
    e ``invoice_gross = delivery_gross``, con IVA calculado por código de industria del proveedor.

    Args:
        base_seq: Número de secuencia base los IDs se asignan como
            ``DOC-{base_seq:09d}`` (ORDER), ``+1`` (DESADV), ``+2`` (INVOICE).
        rng: Generador pseudoaleatorio con semilla fija para reproducibilidad.
        pair: Par proveedor-comprador con condiciones contractuales (lead time, términos de pago).
        supplier_profile: Perfil del proveedor (código de industria para el cálculo del IVA).
        buyer_profile: Perfil del comprador (usado por helpers de importes).
        order_issue: Fecha de emisión del ORDER (punto de anclaje temporal de la tripleta).
        order_gross: Importe bruto del pedido en euros.

    Returns:
        Lista de tres dicts con las filas CSV listas para escribir:
            ``[order_row, desadv_row, invoice_row]``.
    """
    delay_days = _calculate_delay_days(pair.reliability_score, rng)
    delivery_issue = order_issue + timedelta(days=pair.lead_time_days + delay_days)
    invoice_issue = delivery_issue + timedelta(days=rng.randint(0, 2))

    fulfillment_ratio = rng.uniform(0.96, 1.00)
    delivery_gross = round(order_gross * fulfillment_ratio, 2)
    invoice_gross = delivery_gross
    
    tax_rate = _tax_rate_for_industry(supplier_profile.industry_code, rng)
    order_tax = round(order_gross * tax_rate, 2)
    delivery_tax = round(delivery_gross * tax_rate, 2)
    invoice_tax = round(invoice_gross * tax_rate, 2)

    order_total = round(order_gross + order_tax, 2)
    delivery_total = round(delivery_gross + delivery_tax, 2)
    invoice_total = round(invoice_gross + invoice_tax, 2)

    currency = "EUR"
    
    order_id  = f"DOC-{base_seq:09d}"
    desadv_id = f"DOC-{base_seq + 1:09d}"

    # 1. ORDER (Pedido)
    order = {
        "document_id:ID(Document)": order_id,
        "doc_type:string": "ORDER",
        "edi_standard:string": rng.choice(EDI_STANDARDS),
        "version_number:int": 1,
        "issue_date:datetime": order_issue.isoformat(),
        "due_date:datetime": "",
        "status:string": rng.choice(["OPEN", "ACCEPTED", "PARTIALLY_CONFIRMED"]),
        "discrepancy_flag:boolean": rng.choices([True, False], weights=[0.03, 0.97], k=1)[0],
        "currency:string": currency,
        "gross_amount:float": order_gross,
        "tax_amount:float": order_tax,
        "total_amount:float": order_total,
        "payment_terms_days:int": pair.payment_terms_days,
        "contract_type:string": pair.contract_type,
        "lead_time_days:int": pair.lead_time_days,
        "created_at:datetime": datetime.combine(order_issue, datetime.min.time(), tzinfo=UTC).replace(hour=10).isoformat(),
        "supplier_company_id:string": pair.supplier_company_id,
        "buyer_company_id:string": pair.buyer_company_id,
        "delay_days:int": 0,
        "reference_id:string": "",
    }
    
    # 2. DESADV (Albarán)
    desadv = {
        "document_id:ID(Document)": f"DOC-{base_seq + 1:09d}",
        "doc_type:string": "DESADV",
        "edi_standard:string": rng.choice(EDI_STANDARDS),
        "version_number:int": 1,
        "issue_date:datetime": delivery_issue.isoformat(),
        "due_date:datetime": "",
        "status:string": rng.choice(["SHIPPED", "DELIVERED", "PARTIALLY_DELIVERED"]),
        "discrepancy_flag:boolean": rng.choices([True, False], weights=[0.04, 0.96], k=1)[0],
        "currency:string": currency,
        "gross_amount:float": delivery_gross,
        "tax_amount:float": delivery_tax,
        "total_amount:float": delivery_total,
        "payment_terms_days:int": pair.payment_terms_days,
        "contract_type:string": pair.contract_type,
        "lead_time_days:int": pair.lead_time_days,
        "created_at:datetime": datetime.combine(delivery_issue, datetime.min.time(), tzinfo=UTC).replace(hour=10).isoformat(),
        "supplier_company_id:string": pair.supplier_company_id,
        "buyer_company_id:string": pair.buyer_company_id,
        "delay_days:int": delay_days,
        "reference_id:string": order_id,
    }
    
    # 3. INVOICE (Factura)
    invoice = {
        "document_id:ID(Document)": f"DOC-{base_seq + 2:09d}",
        "doc_type:string": "INVOICE",
        "edi_standard:string": rng.choice(EDI_STANDARDS),
        "version_number:int": 1,
        "issue_date:datetime": invoice_issue.isoformat(),
        "due_date:datetime": (invoice_issue + timedelta(days=pair.payment_terms_days)).isoformat(),
        "status:string": rng.choice(["ISSUED", "SENT", "PAID", "OVERDUE"]),
        "discrepancy_flag:boolean": rng.choices([True, False], weights=[0.06, 0.94], k=1)[0],
        "currency:string": currency,
        "gross_amount:float": invoice_gross,
        "tax_amount:float": invoice_tax,
        "total_amount:float": invoice_total,
        "payment_terms_days:int": pair.payment_terms_days,
        "contract_type:string": pair.contract_type,
        "lead_time_days:int": pair.lead_time_days,
        "created_at:datetime": datetime.combine(invoice_issue, datetime.min.time(), tzinfo=UTC).replace(hour=10).isoformat(),
        "supplier_company_id:string": pair.supplier_company_id,
        "buyer_company_id:string": pair.buyer_company_id,
        "delay_days:int": delay_days,
        "reference_id:string": desadv_id,
    }

    return [order, desadv, invoice]


# =============================================================================
#  FUNCIONES AUXILIARES (Helpers / Utils)
# =============================================================================

def _determine_order_frequency(contract_type: str, rng: random.Random) -> int:
    """Determina la frecuencia anual base de pedidos según el tipo de contrato.

    Args:
        contract_type: Tipo de contrato (``SPOT``, ``ANNUAL``, ``FRAME`` o ``MULTIYEAR``).
        rng: Generador aleatorio inicializado con la semilla global.

    Returns:
        Número entero de pedidos anuales base antes de aplicar el multiplicador de escala.
    """
    if contract_type == "SPOT":
        return rng.randint(1, 3)
    if contract_type == "ANNUAL":
        return rng.choices([1, 2], weights=[0.75, 0.25], k=1)[0]
    return rng.randint(4, 12)


def _apply_frequency_scale(base_orders: int, avg_out_degree: int) -> int:
    """Escala la frecuencia base de pedidos proporcionalmente al grado de salida medio.

    Args:
        base_orders: Frecuencia anual base devuelta por ``_determine_order_frequency``.
        avg_out_degree: Multiplicador de frecuencia configurado en el CLI (``--avg-degree-documents``).

    Returns:
        Número entero de pedidos anuales escalado, mínimo 1.
    """
    scale = max(avg_out_degree, 1) / 5.0
    return max(1, int(round(base_orders * scale)))


def _distribute_dates_with_seasonality(start_date: date, end_date: date, num_dates: int, rng: random.Random) -> list[date]:
    """Distribuye fechas forzando la primera en ``start_date`` y el resto con sesgo estacional.

    Args:
        start_date: Fecha de inicio del periodo activo (primera fecha garantizada).
        end_date: Límite superior del periodo; ninguna fecha lo supera.
        num_dates: Número total de fechas a generar.
        rng: Generador aleatorio inicializado con la semilla global.

    Returns:
        Lista de ``num_dates`` fechas ordenadas ascendentemente dentro del periodo.
    """
    if num_dates <= 0:
        return []
    if num_dates == 1:
        return [start_date]

    window_days = (end_date - start_date).days
    if window_days <= 0:
        return [start_date] * num_dates

    # El primer documento siempre desencadena la relación en start_date
    picked: list[date] = [start_date]
    remaining_dates = num_dates - 1
    
    max_attempts = max(500, remaining_dates * 40)
    attempts = 0

    # Distribuimos el resto a lo largo del periodo activo
    while len(picked) < num_dates and attempts < max_attempts:
        attempts += 1
        candidate = start_date + timedelta(days=rng.randint(1, window_days)) # Evitamos el dia 0 porque ya está
        acceptance = MONTH_WEIGHTS.get(candidate.month, 1.0) / MAX_MONTH_WEIGHT
        if rng.random() <= acceptance:
            picked.append(candidate)

    while len(picked) < num_dates:
        picked.append(start_date + timedelta(days=rng.randint(1, window_days)))

    return sorted(picked)


def _distribute_volume(total_volume: float, num_orders: int, rng: random.Random) -> list[float]:
    """Distribuye un volumen total entre ``num_orders`` pedidos usando cortes aleatorios uniformes.

    Args:
        total_volume: Importe total a repartir entre todos los pedidos (€).
        num_orders: Número de pedidos entre los que dividir el volumen.
        rng: Generador aleatorio inicializado con la semilla global.

    Returns:
        Lista de ``num_orders`` importes redondeados a 2 decimales que suman ``total_volume``.
    """
    if num_orders <= 1:
        return [round(max(total_volume, 0.01), 2)]
    cuts = sorted(rng.random() for _ in range(num_orders - 1))
    cuts = [0.0] + cuts + [1.0]
    raw_amounts = [max(total_volume * (cuts[i + 1] - cuts[i]), 0.01) for i in range(num_orders)]
    rounded = [round(amount, 2) for amount in raw_amounts]
    expected_total = round(total_volume, 2)
    diff = round(expected_total - sum(rounded), 2)
    rounded[-1] = round(max(0.01, rounded[-1] + diff), 2)
    return rounded


def _calculate_delay_days(reliability_score: float, rng: random.Random) -> int:
    """Calcula el retraso de entrega en días según la fiabilidad del proveedor.

    Args:
        reliability_score: Fiabilidad contractual del proveedor en ``[0, 1]``.
            Con probabilidad ``reliability_score`` no hay retraso.
        rng: Generador aleatorio inicializado con la semilla global.

    Returns:
        Número entero de días de retraso, 0 si la entrega es puntual.
    """
    if rng.random() < reliability_score:
        return 0
    max_delay = int((1.0 - reliability_score) * 20) + 2
    return rng.randint(1, max_delay)


def _tax_rate_for_industry(industry_code: str, rng: random.Random) -> float:
    """Selecciona el tipo de IVA aplicable según el código NACE de la industria.

    Args:
        industry_code: Código NACE del proveedor emisor (p. ej. ``C10``, ``G46``).
        rng: Generador aleatorio inicializado con la semilla global.

    Returns:
        Tipo de IVA como fracción decimal (p. ej. ``0.21`` para el 21 %).
    """
    rates = INDUSTRY_TAX_RATES.get(industry_code, [0.21])
    return rng.choice(rates)
