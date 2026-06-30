# Empresas (`companies_synthesizer.py`)

Genera `companies.csv` usando el modelo LFR para producir comunidades con
distribuciones de grado power-law realistas, ancladas geográficamente a
municipios reales de España.

---

## Modelos de datos

::: backend.etl.generation.companies_synthesizer.MunicipalityPoint
    options:
      show_root_full_path: false

::: backend.etl.generation.companies_synthesizer.LFRProfile
    options:
      show_root_full_path: false

---

## Función principal

::: backend.etl.generation.companies_synthesizer.synthesize_companies_csv
    options:
      show_root_full_path: false

::: backend.etl.generation.companies_synthesizer.load_municipalities
    options:
      show_root_full_path: false