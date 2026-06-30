"""Sintetizador de líneas de documento CONTAINS entre documentos y productos.

Genera ``rel_contains.csv`` leyendo ``documents.csv`` en modo streaming y
asociando a cada triplet (ORDER → DESADV → INVOICE) los productos del
catálogo del proveedor correspondiente, con precios, descuentos y fechas de
entrega coherentes con el documento raíz.
"""
from __future__ import annotations

import csv
import random
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
import typing
from backend.etl.generation.csv_templates import CSV_SCHEMAS
from backend.core.utils import safe_float, safe_int, safe_date, pick

# =============================================================================
# CABECERA (Configuracion y catalogo)
# =============================================================================
DOC_TYPE_RANK = {
    "ORDER": 0,
    "DESADV": 1,
    "INVOICE": 2,
}

DOC_TYPE_LINE_STATUS = {
    "ORDER": "OPEN",
    "DESADV": "SHIPPED",
    "INVOICE": "BILLED",
}


@dataclass(frozen=True)
class ProductRecord:
    """Datos mínimos de producto necesarios para generar líneas CONTAINS.

    Attributes:
        product_id: Identificador único del producto.
        supplier_company_id: ID del proveedor que lo suministra.
        base_price: Precio base unitario en euros.
        lead_time_baseline_days: Plazo de entrega base en días.
        criticality: Nivel de criticidad: ``LOW``, ``MEDIUM`` o ``HIGH``.
        unit: Unidad de medida.
    """

    product_id: str
    supplier_company_id: str
    base_price: float
    lead_time_baseline_days: int
    criticality: str
    unit: str


@dataclass(frozen=True)
class DocumentRecord:
    """Datos mínimos de documento necesarios para generar líneas CONTAINS.

    Attributes:
        document_id: Identificador único del documento.
        doc_type: Tipo de documento: ``ORDER``, ``DESADV`` o ``INVOICE``.
        issue_date: Fecha de emisión.
        gross_amount: Importe bruto en euros.
        supplier_company_id: ID del proveedor emisor.
        reference_id: ID del ORDER raíz (vacío para el propio ORDER).
    """

    document_id: str
    doc_type: str
    issue_date: date
    gross_amount: float
    supplier_company_id: str
    reference_id: str


@dataclass(frozen=True)
class LineBlueprint:
    """Datos inmutable de una línea, compartido entre los tres documentos del triplete.

    Attributes:
        product_id: Identificador del producto de la línea.
        lot_number: Número de lote asignado a la línea.
        unit_price: Precio unitario en euros (con variación sobre ``base_price``).
        discount_pct: Porcentaje de descuento.
        expected_delivery_date: Fecha esperada de entrega desde el ``issue_date`` del ORDER.
        weight: Peso proporcional de esta línea sobre el total del documento.
    """

    product_id: str
    lot_number: str
    unit_price: float
    discount_pct: float
    expected_delivery_date: date
    weight: float


# =============================================================================
# INTERFAZ PUBLICA (CLI)
# =============================================================================


# =============================================================================
# FUNCION PRINCIPAL (MAIN)
# =============================================================================
def synthesize_rel_contains_csv(output_file: Path, documents_csv: Path, products_csv: Path, seed: int) -> Path:
    """Genera rel_contains.csv con líneas de documento en modo streaming.

    Lee ``documents.csv`` aprovechando el orden secuencial de los tripletas
    (ORDER → DESADV → INVOICE) para procesar cada cadena.

    Args:
        output_file: Ruta del fichero CSV de salida.
        documents_csv: Ruta al CSV de documentos generado previamente.
        products_csv: Ruta al CSV de productos generado previamente.
        seed: Semilla para reproducibilidad.

    Returns:
        Ruta al fichero CSV escrito.

    Raises:
        FileNotFoundError: Si ``documents_csv`` o ``products_csv`` no existen.
        ValueError: Si no hay productos para el proveedor de algún documento.
    """
    rng = random.Random(seed)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # documents = _load_documents(documents_csv)
    products_by_supplier = _load_products_by_supplier(products_csv)

    fieldnames = CSV_SCHEMAS["rel_contains.csv"]

    with output_file.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        # for root_document, chain_documents in _group_documents_by_traceability(documents):
        for root_document, chain_documents in _stream_document_chains(documents_csv):
            catalog = products_by_supplier.get(root_document.supplier_company_id, [])
            if not catalog:
                raise ValueError(
                    f"No hay productos para el proveedor {root_document.supplier_company_id} requerido por {root_document.document_id}."
                )

            blueprints = _build_line_blueprints(root_document, catalog, rng)
            weights = [blueprint.weight for blueprint in blueprints]

            for document in chain_documents:
                line_amounts = _allocate_amounts(document.gross_amount, weights)
                for line_index, (blueprint, line_amount) in enumerate(zip(blueprints, line_amounts), start=1):
                    net_unit_price = blueprint.unit_price * (1.0 - blueprint.discount_pct)
                    quantity = round(max(line_amount / max(net_unit_price, 0.01), 0.001), 4)
                    writer.writerow(
                        {
                            "line_id:string": f"{document.document_id}-L{line_index:03d}",
                            "lot_number:string": blueprint.lot_number,
                            "quantity:float": quantity,
                            "unit_price:float": round(blueprint.unit_price, 4),
                            "discount_pct:float": round(blueprint.discount_pct, 4),
                            "line_amount:float": round(line_amount, 2),
                            "line_status:string": DOC_TYPE_LINE_STATUS.get(document.doc_type, "OPEN"),
                            "expected_delivery_date:datetime": blueprint.expected_delivery_date.isoformat(),
                            ":START_ID(Document)": document.document_id,
                            ":END_ID(Product)": blueprint.product_id,
                            ":TYPE": "CONTAINS",
                        }
                    )

    return output_file

# =============================================================================
# FUNCIONES AUXILIARES (Helpers / Utils)
# =============================================================================
def _stream_document_chains(documents_csv: Path) -> typing.Iterator[tuple[DocumentRecord, list[DocumentRecord]]]:
    """Lee documents.csv en streaming agrupando filas en cadenas de trazabilidad.

    Aprovecha que los tripletas (ORDER → DESADV → INVOICE) se escribieron de
    forma contigua para detectar cambios de cadena comparando ``reference_id``
    sin cargar todo el fichero en memoria.

    Args:
        documents_csv: Ruta al CSV de documentos.

    Yields:
        Documento raíz (ORDER) y lista completa de documentos de la cadena.

    Raises:
        FileNotFoundError: Si ``documents_csv`` no existe.
    """
    if not documents_csv.exists():
        raise FileNotFoundError(f"No existe documents.csv: {documents_csv}")

    current_chain: list[DocumentRecord] = []
    current_root_id: str | None = None
    id_to_root: dict[str, str] = {}  # resuelve referencias multi-salto al root de la cadena

    with documents_csv.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            document_id = (pick(row, "document_id:ID(Document)", "document_id") or "").strip()
            if not document_id:
                continue

            doc = DocumentRecord(
                document_id=document_id,
                doc_type=(pick(row, "doc_type:string", "doc_type") or "ORDER").strip().upper(),
                issue_date=safe_date(pick(row, "issue_date:datetime", "issue_date"), date(2026, 1, 1)),
                gross_amount=max(safe_float(pick(row, "gross_amount:float", "gross_amount"), 0.0), 0.0),
                supplier_company_id=(pick(row, "supplier_company_id:string", "supplier_company_id") or "").strip(),
                reference_id=(pick(row, "reference_id:string", "reference_id") or "").strip(),
            )

            # Resolvemos el root siguiendo referencias multi-salto (INVOICE → DESADV → ORDER)
            if not doc.reference_id:
                root_id = doc.document_id
            else:
                root_id = id_to_root.get(doc.reference_id, doc.reference_id)
            id_to_root[doc.document_id] = root_id

            if current_root_id is None:
                current_root_id = root_id
                current_chain.append(doc)
            elif root_id == current_root_id:
                current_chain.append(doc)
            else:
                # Cambio de cadena: Yield de la cadena anterior y reset
                root_doc = next((d for d in current_chain if d.doc_type == "ORDER"), current_chain[0])
                yield root_doc, current_chain

                current_root_id = root_id
                current_chain = [doc]
                id_to_root = {doc.document_id: root_id}

        # No olvidar hacer yield de la última cadena al terminar el archivo
        if current_chain:
            root_doc = next((d for d in current_chain if d.doc_type == "ORDER"), current_chain[0])
            yield root_doc, current_chain
            
# def _load_documents(documents_csv: Path) -> list[DocumentRecord]:
#     """Carga documentos desde un CSV, validando y limpiando los datos."""
#     if not documents_csv.exists():
#         raise FileNotFoundError(f"No existe documents.csv: {documents_csv}")

#     documents: list[DocumentRecord] = []
#     with documents_csv.open("r", encoding="utf-8", newline="") as csv_file:
#         reader = csv.DictReader(csv_file)
#         for row in reader:
#             document_id = (row.get("document_id") or "").strip()
#             if not document_id:
#                 continue
#             documents.append(
#                 DocumentRecord(
#                     document_id=document_id,
#                     doc_type=(row.get("doc_type") or "ORDER").strip().upper(),
#                     issue_date=safe_date(row.get("issue_date"), date(2026, 1, 1)),
#                     gross_amount=max(safe_float(row.get("gross_amount"), 0.0), 0.0),
#                     supplier_company_id=(row.get("supplier_company_id") or "").strip(),
#                     reference_id=(row.get("reference_id") or "").strip(),
#                 )
#             )

#     return documents


def _load_products_by_supplier(products_csv: Path) -> dict[str, list[ProductRecord]]:
    """Carga productos desde un CSV, organizándolos por proveedor y validando los datos."""
    if not products_csv.exists():
        raise FileNotFoundError(f"No existe products.csv: {products_csv}")

    products_by_supplier: dict[str, list[ProductRecord]] = {}
    with products_csv.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            product_id = (pick(row, "product_id:ID(Product)", "product_id") or "").strip()
            supplier_company_id = (pick(row, "supplier_company_id:string", "supplier_company_id") or "").strip()
            if not product_id or not supplier_company_id:
                continue
            products_by_supplier.setdefault(supplier_company_id, []).append(
                ProductRecord(
                    product_id=product_id,
                    supplier_company_id=supplier_company_id,
                    base_price=max(safe_float(pick(row, "base_price:float", "base_price"), 1.0), 0.01),
                    lead_time_baseline_days=max(safe_int(pick(row, "lead_time_baseline_days:int", "lead_time_baseline_days"), 1), 0),
                    criticality=(pick(row, "criticality:string", "criticality") or "MEDIUM").strip().upper(),
                    unit=(pick(row, "unit:string", "unit") or "unit").strip(),
                )
            )

    return products_by_supplier


# def _group_documents_by_traceability(documents: list[DocumentRecord]) -> list[tuple[DocumentRecord, list[DocumentRecord]]]:
#     """Agrupa documentos en cadenas de trazabilidad, ordenando por tipo y fecha."""
#     groups: dict[str, list[DocumentRecord]] = {}
#     ordered_roots: list[str] = []

#     for document in documents:
#         root_id = document.document_id if not document.reference_id else document.reference_id
#         if root_id not in groups:
#             groups[root_id] = []
#             ordered_roots.append(root_id)
#         groups[root_id].append(document)

#     result: list[tuple[DocumentRecord, list[DocumentRecord]]] = []
#     for root_id in ordered_roots:
#         chain_documents = sorted(groups[root_id], key=lambda doc: (DOC_TYPE_RANK.get(doc.doc_type, 99), doc.issue_date, doc.document_id))
#         root_document = next((doc for doc in chain_documents if doc.doc_type == "ORDER"), chain_documents[0])
#         result.append((root_document, chain_documents))

#     return result


def _build_line_blueprints(root_document: DocumentRecord, catalog: list[ProductRecord], rng: random.Random) -> list[LineBlueprint]:
    """Construye blueprints de líneas para un documento raíz, seleccionando productos y asignando precios y fechas."""
    num_lines = _determine_line_count(root_document.gross_amount, len(catalog), rng)
    selected_products = _weighted_sample_without_replacement(catalog, num_lines, rng)
    weights = [max(product.base_price * rng.uniform(0.7, 1.3), 0.01) for product in selected_products]
    weights_total = sum(weights) or float(len(weights))
    normalized_weights = [weight / weights_total for weight in weights]

    blueprints: list[LineBlueprint] = []
    for line_index, (product, weight) in enumerate(zip(selected_products, normalized_weights), start=1):
        base_multiplier = rng.uniform(0.92, 1.12)
        if product.criticality == "HIGH":
            base_multiplier *= 1.10
        elif product.criticality == "LOW":
            base_multiplier *= 0.95

        unit_price = max(round(product.base_price * base_multiplier, 4), 0.01)
        discount_pct = round(rng.uniform(0.0, 0.18), 4)
        expected_delivery_date = root_document.issue_date + timedelta(days=max(product.lead_time_baseline_days, 0))

        blueprints.append(
            LineBlueprint(
                product_id=product.product_id,
                lot_number=f"LOT-{root_document.document_id[-6:]}-{line_index:02d}",
                unit_price=unit_price,
                discount_pct=discount_pct,
                expected_delivery_date=expected_delivery_date,
                weight=weight,
            )
        )

    return blueprints


def _determine_line_count(gross_amount: float, catalog_size: int, rng: random.Random) -> int:
    """Determina el número de líneas para un documento dado su monto bruto y el tamaño del catálogo del proveedor."""
    if catalog_size <= 1:
        return 1

    if gross_amount < 500:
        base = 1
    elif gross_amount < 2_500:
        base = 2
    elif gross_amount < 10_000:
        base = 3
    elif gross_amount < 50_000:
        base = 4
    else:
        base = 5

    base += rng.choice([-1, 0, 0, 1])
    return max(1, min(base, min(catalog_size, 8)))


def _weighted_sample_without_replacement(records: list[ProductRecord], sample_size: int, rng: random.Random) -> list[ProductRecord]:
    """Realiza un muestreo ponderado sin reemplazo de registros, basado en el precio base."""
    available = records[:]
    selected: list[ProductRecord] = []
    while available and len(selected) < sample_size:
        weights = [max(record.base_price, 0.01) for record in available]
        picked = rng.choices(available, weights=weights, k=1)[0]
        selected.append(picked)
        available.remove(picked)
    return selected


def _allocate_amounts(total_amount: float, weights: list[float]) -> list[float]:
    """Asigna montos a líneas basado en pesos, asegurando que la suma sea igual al monto total."""
    if not weights:
        return []
    if len(weights) == 1:
        return [round(max(total_amount, 0.0), 2)]

    weights_total = sum(weights) or float(len(weights))
    normalized = [weight / weights_total for weight in weights]
    rounded = [round(max(total_amount * share, 0.01), 2) for share in normalized]
    diff = round(total_amount - sum(rounded), 2)
    rounded[-1] = round(max(0.01, rounded[-1] + diff), 2)
    return rounded