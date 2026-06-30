# Líneas de Documento (`rel_contains_synthesizer.py`)

Genera `rel_contains.csv` leyendo `documents.csv` en modo streaming y
asociando a cada tripleta (ORDER → DESADV → INVOICE) los productos del
catálogo del proveedor correspondiente, con precios, descuentos y fechas de
entrega coherentes con el documento raíz.

---

## Modelos de datos

::: backend.etl.generation.rel_contains_synthesizer.ProductRecord
    options:
      show_root_full_path: false

::: backend.etl.generation.rel_contains_synthesizer.DocumentRecord
    options:
      show_root_full_path: false

::: backend.etl.generation.rel_contains_synthesizer.LineBlueprint
    options:
      show_root_full_path: false

---

## Función principal

::: backend.etl.generation.rel_contains_synthesizer.synthesize_rel_contains_csv
    options:
      show_root_full_path: false

### Generador interno

::: backend.etl.generation.rel_contains_synthesizer._stream_document_chains
    options:
      show_root_full_path: false