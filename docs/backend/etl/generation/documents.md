# Documentos (`documents_synthesizer.py`)

Genera `documents.csv` produciendo tripletas EDI coherentes (ORDER → DESADV →
INVOICE) con distribución temporal realista, importes correlacionados y flags
de discrepancia. El generador interno opera en modo streaming (O(1) memoria).

---

## Modelos de datos

::: backend.etl.generation.documents_synthesizer.CompanyProfile
    options:
      show_root_full_path: false

::: backend.etl.generation.documents_synthesizer.CompanyPair
    options:
      show_root_full_path: false

---

## Función principal

::: backend.etl.generation.documents_synthesizer.synthesize_documents_csv
    options:
      show_root_full_path: false

### Generador interno

::: backend.etl.generation.documents_synthesizer._document_stream_generator
    options:
      show_root_full_path: false