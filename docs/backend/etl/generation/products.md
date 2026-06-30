# Productos (`products_synthesizer.py`)

Genera `products.csv` asignando a cada proveedor un catálogo proporcional a
su peso en la red (`baseline_revenue`, `out_degree`, `agreed_volume_total`).
La categoría de cada producto se elige según probabilidades previas por código
NACE definidas en `INDUSTRY_CATEGORY_PRIORS`.

---

## Modelos de datos

::: backend.etl.generation.products_synthesizer.SupplierProfile
    options:
      show_root_full_path: false

---

## Función principal

::: backend.etl.generation.products_synthesizer.synthesize_products_csv
    options:
      show_root_full_path: false