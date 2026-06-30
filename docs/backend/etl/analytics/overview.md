# Motor Analítico B2B

`B2BGraphAnalyzer` es la clase raíz del subsistema analítico. Agrega cuatro mixins
especializados mediante herencia múltiple y gestiona el ciclo de vida de la conexión
Neo4j, exponiendo `_fetch_data` como helper de lectura compartido por todos ellos.

---

::: backend.etl.analytics.analyzer.B2BGraphAnalyzer
    options:
      inherited_members: false
      show_root_full_path: false

---

## Helper de errores

::: backend.etl.analytics.analyzer._report_query_error
    options:
      show_root_full_path: false