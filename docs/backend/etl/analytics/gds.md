# Analítica de Grafos — GDS (`gds.py`)

`GDSMixin` envuelve los algoritmos de Neo4j Graph Data Science sobre la red `SUPPLIES`.
Todos los métodos siguen el ciclo **project → compute → drop** gestionado por `_run_gds`,
que garantiza la limpieza de proyecciones en memoria aunque el cálculo falle.

---

## Mixin

::: backend.etl.analytics.gds.GDSMixin
    options:
      show_root_full_path: false