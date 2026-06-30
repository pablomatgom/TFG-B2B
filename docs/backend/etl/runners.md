# Runners del Pipeline ETL

Los runners orquestan las tres fases del pipeline y el paso de seeding.
Cada runner es independiente: puede invocarse directamente desde la CLI o
ser llamado en cadena por `run_all`.

```
run_all
 ├── run_generate   →   data/synthetic/*.csv
 ├── run_load       →   Neo4j (grafo poblado)
 ├── run_analyze    →   data/export/*.json
 └── run_seed       →   data/users.db (usuarios demo)
```

Cada paso escribe un artefacto JSON en `data/processed/<step>_last_run.json`
con marca temporal, métricas y estado de la ejecución.

---

## Orquestador principal (`run_all.py`)

::: backend.etl.runners.run_all.run_all
    options:
      show_root_full_path: false

---

## Fase 1 - Generación (`run_generate.py`)

::: backend.etl.runners.run_generate.run_generate
    options:
      show_root_full_path: false

---

## Fase 2 - Carga (`run_load.py`)

::: backend.etl.runners.run_load.run_load
    options:
      show_root_full_path: false

---

## Fase 3 - Analítica (`run_analyze.py`)

::: backend.etl.runners.run_analyze.run_analyze
    options:
      show_root_full_path: false

### Helpers de tolerancia a fallos

::: backend.etl.runners.run_analyze._safe_df
    options:
      show_root_full_path: false

::: backend.etl.runners.run_analyze._safe_dict
    options:
      show_root_full_path: false

---

## Fase optativa de Seeding (`run_seed.py`)

::: backend.etl.runners.run_seed.run_seed
    options:
      show_root_full_path: false
