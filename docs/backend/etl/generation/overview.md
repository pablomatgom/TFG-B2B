# Sintetizadores de Datos - Visión General

Los sintetizadores generan los cinco CSVs del modelo B2B en orden estricto
de dependencia. Cada módulo es independiente y autocontenido.

```
companies.csv
    └── rel_supplies.csv   (requiere companies.csv)
            └── products.csv    (requiere companies + rel_supplies)
            └── documents.csv   (requiere companies + rel_supplies)
                    └── rel_contains.csv  (requiere documents + products)
```

---

## Esquemas CSV (`csv_templates.py`)

Fuente única de verdad para los nombres y tipos de columna de los cinco datasets.

### `companies.csv`
| Campo | Tipo |
|---|---|
| `company_id` | `ID(Company)` |
| `legal_name`, `tax_id`, `edi_endpoint`, `node_role` | `string` |
| `country`, `region`, `city` | `string` |
| `latitude`, `longitude` | `float` |
| `industry_code`, `size_band` | `string` |
| `baseline_revenue` | `float` |
| `created_at` | `datetime` |
| `is_active` | `boolean` |

### `rel_supplies.csv`
| Campo | Tipo |
|---|---|
| `:START_ID(Company)`, `:END_ID(Company)` | edge endpoints |
| `since_date` | `datetime` |
| `lead_time_days`, `payment_terms_agreed` | `int` |
| `reliability_score`, `agreed_volume_baseline` | `float` |
| `is_exclusive_supplier` | `boolean` |
| `contract_type` | `string` |
| `:TYPE` | `SUPPLIES` |

### `products.csv`
| Campo | Tipo |
|---|---|
| `product_id` | `ID(Product)` |
| `sku`, `hs_code`, `name`, `category`, `unit` | `string` |
| `base_price` | `float` |
| `lead_time_baseline_days` | `int` |
| `criticality` | `string` |
| `is_substitutable` | `boolean` |
| `supplier_company_id` | `string` |

### `documents.csv`
| Campo | Tipo |
|---|---|
| `document_id` | `ID(Document)` |
| `doc_type`, `edi_standard`, `status` | `string` |
| `version_number`, `payment_terms_days`, `lead_time_days`, `delay_days` | `int` |
| `issue_date`, `due_date`, `created_at` | `datetime` |
| `discrepancy_flag` | `boolean` |
| `currency`, `contract_type` | `string` |
| `gross_amount`, `tax_amount`, `total_amount` | `float` |
| `supplier_company_id`, `buyer_company_id`, `reference_id` | `string` |

### `rel_contains.csv`
| Campo | Tipo |
|---|---|
| `line_id`, `lot_number`, `line_status` | `string` |
| `quantity`, `unit_price`, `discount_pct`, `line_amount` | `float` |
| `expected_delivery_date` | `datetime` |
| `:START_ID(Document)`, `:END_ID(Product)` | edge endpoints |
| `:TYPE` | `CONTAINS` |

---

## Utilidades de esquema

::: backend.etl.generation.csv_templates.create_csv_templates
    options:
      show_root_full_path: false

::: backend.etl.generation.csv_templates.resolve_csv_targets
    options:
      show_root_full_path: false

::: backend.etl.generation.csv_templates.get_available_targets
    options:
      show_root_full_path: false