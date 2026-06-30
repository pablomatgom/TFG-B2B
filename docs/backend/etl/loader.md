# Cargador Neo4j — Bulk Loader

Módulo responsable de la ingesta masiva de los CSVs sintéticos en el grafo
Neo4j.  Implementa un pipeline de carga por lotes con gestión de constraints,
índices y trazabilidad de rendimiento.

---

## Estadísticas de carga (`LoadStats`)

::: backend.etl.loader.LoadStats
    options:
      show_root_full_path: false

---

## Cargador principal (`Neo4jBulkLoader`)

### Orden de carga obligatorio

| Paso | Fichero | Nodos / Relaciones creados |
|---|---|---|
| 1 | `companies.csv` | Nodos `Company` |
| 2 | `rel_supplies.csv` | Aristas `SUPPLIES` |
| 3 | `products.csv` | Nodos `Product` + aristas `SELLS` |
| 4 | `documents.csv` | Nodos `Document` + `ISSUES`, `SENT_TO`, `Issue_on`, `FULFILLS` |
| 5 | `rel_contains.csv` | Aristas `CONTAINS` |

### Constraints e índices

| Tipo | Entidad | Campo(s) |
|---|---|---|
| UNIQUE | `Company` | `company_id` |
| UNIQUE | `Product` | `product_id` |
| UNIQUE | `Document` | `document_id` |
| UNIQUE | `TimeBucket` | `date` |
| INDEX | `Company` | `node_role`, `region`, `industry_code` |
| INDEX | `Product` | `hs_code`, `criticality` |
| INDEX | `Document` | `doc_type`, `contract_type`, `discrepancy_flag`, `(doc_type, discrepancy_flag)` |

### Métodos públicos

::: backend.etl.loader.Neo4jBulkLoader
    options:
      show_root_full_path: false
      members:
        - verify_connection
        - create_constraints_and_indexes
        - clear_database
        - load_from_directory
        - close

### Métodos internos

::: backend.etl.loader.Neo4jBulkLoader._load_csv_dataset
    options:
      show_root_full_path: false

::: backend.etl.loader.Neo4jBulkLoader._iter_csv_batches
    options:
      show_root_full_path: false

::: backend.etl.loader.Neo4jBulkLoader._write_batch
    options:
      show_root_full_path: false

::: backend.etl.loader.Neo4jBulkLoader._clean_key
    options:
      show_root_full_path: false