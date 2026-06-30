# Trazabilidad Documental (`traceability.py`)

`LineageMixin` implementa tres patrones de búsqueda sobre las relaciones `FULFILLS` 
(hasta 5 saltos): rastreo hacia atrás (desde facturas con discrepancias hasta su 
pedido original), extracción del camino exacto para garantizar la trazabilidad 
paso a paso, y exploración hacia adelante (desde el pedido base hacia todo el 
flujo de documentos generados posteriormente).

---

## Mixin

::: backend.etl.analytics.traceability.LineageMixin
    options:
      show_root_full_path: false