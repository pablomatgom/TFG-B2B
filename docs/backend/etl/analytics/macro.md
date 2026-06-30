# Métricas Macroscópicas (`macro_stats.py`)

`MacroMixin` evalúa el estado del grafo de forma global: estructura de nodos y aristas,
rankings de proveedores y compradores, distribución temporal de documentos EDI y validación
de la topología scale-free mediante el coeficiente de Gini y el umbral de hubs.

---

## Modelo de datos

::: backend.etl.analytics.macro_stats.GraphMacroStats
    options:
      show_root_full_path: false

---

## Mixin

::: backend.etl.analytics.macro_stats.MacroMixin
    options:
      show_root_full_path: false