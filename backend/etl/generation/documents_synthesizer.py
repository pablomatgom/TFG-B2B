from __future__ import annotations

import argparse
import csv
import logging
import random
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
    company_id: str
    country: str
    industry_code: str
    baseline_revenue: float

@dataclass(frozen=True)
class CompanyPair:
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
    """Genera documents.csv abarcando todo el historial usando un generador."""
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
        logging.warning("No se han generado documentos; revisa since_date en rel_supplies.csv")
    else:
        # Opcional: Un log para que veas en consola cuántos se generaron
        logging.info(f"Éxito: Se han generado {docs_generated} documentos en modo streaming.")

    return output_file


# =============================================================================
#  LÓGICA DE ALTO NIVEL (Cargas y Generadores Complejos)
# =============================================================================
def _load_company_profiles(companies_csv: Path) -> dict[str, CompanyProfile]:
    """Carga de perfiles de empresa desde companies.csv."""
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
    """Carga de contratos desde rel_supplies.csv."""
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
                               rng: random.Random, avg_out_degree: int):
    """Generador que emite documentos B2B de uno en uno."""
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
    """Generación de secuencia lógica de 3 documentos: Pedido -> Albarán -> Factura."""
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
    
    order_id = f"DOC-{base_seq:09d}"

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
        "reference_id:string": order_id,
    }

    return [order, desadv, invoice]


# =============================================================================
#  FUNCIONES AUXILIARES (Helpers / Utils)
# =============================================================================

def _determine_order_frequency(contract_type: str, rng: random.Random) -> int:
    if contract_type == "SPOT":
        return rng.randint(1, 3)
    if contract_type == "ANNUAL":
        return rng.choices([1, 2], weights=[0.75, 0.25], k=1)[0]
    return rng.randint(4, 12)


def _apply_frequency_scale(base_orders: int, avg_out_degree: int) -> int:
    scale = max(avg_out_degree, 1) / 5.0
    return max(1, int(round(base_orders * scale)))


def _distribute_dates_with_seasonality(start_date: date, end_date: date, num_dates: int, rng: random.Random) -> list[date]:
    """Distribuye fechas forzando la primera en el start_date, y el resto con sesgo estacional."""
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
    if rng.random() < reliability_score:
        return 0
    max_delay = int((1.0 - reliability_score) * 20) + 2
    return rng.randint(1, max_delay)


def _tax_rate_for_industry(industry_code: str, rng: random.Random) -> float:
    rates = INDUSTRY_TAX_RATES.get(industry_code, [0.21])
    return rng.choice(rates)
