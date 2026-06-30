# Suministros (`supplies_synthesizer.py`)

Genera `rel_supplies.csv` construyendo una red Scale-Free adaptada a la
topología LFR: las aristas intra-comunidad son más probables que las
inter-comunidad, y los nodos con mayor `baseline_revenue` tienen mayor
probabilidad de ser seleccionados como extremos de una arista.

---

## Modelos de datos

::: backend.etl.generation.supplies_synthesizer.CompanyRecord
    options:
      show_root_full_path: false

---

## Función principal

::: backend.etl.generation.supplies_synthesizer.synthesize_rel_supplies_csv
    options:
      show_root_full_path: false

::: backend.etl.generation.supplies_synthesizer.load_companies
    options:
      show_root_full_path: false