# Modelos de la API

Este módulo agrupa todos los esquemas que validan las peticiones entrantes 
y serializan las respuestas de la capa REST.  Se dividen en tres
archivos según el dominio al que pertenecen.

---

## Autenticación (`auth.py`)

Modelos usados por los endpoints de login y registro de usuarios.

::: backend.api.models.auth.LoginRequest
    options:
      show_root_full_path: false

::: backend.api.models.auth.TokenResponse
    options:
      show_root_full_path: false

::: backend.api.models.auth.UserOut
    options:
      show_root_full_path: false

::: backend.api.models.auth.RegisterRequest
    options:
      show_root_full_path: false

---

## Empresa y Documentos (`company.py`)

Modelos para la gestión de perfiles de empresa y el ciclo de vida de
documentos EDI dentro del grafo Neo4j.

::: backend.api.models.company.CompanyProfileUpdate
    options:
      show_root_full_path: false

::: backend.api.models.company.DocumentStatusUpdate
    options:
      show_root_full_path: false

### Estados de documento válidos

| Estado | Descripción |
|---|---|
| `OPEN` | Pedido creado pero aún no confirmado |
| `ACCEPTED` | Pedido aceptado por el proveedor |
| `PARTIALLY_CONFIRMED` | Confirmación parcial de líneas |
| `SHIPPED` | Mercancía expedida |
| `DELIVERED` | Entrega completada |
| `PARTIALLY_DELIVERED` | Entrega parcial |
| `ISSUED` | Factura emitida |
| `SENT` | Factura enviada al destinatario |
| `PAID` | Factura liquidada |
| `OVERDUE` | Factura vencida sin pagar |

---

## Pipeline ETL (`pipeline.py`)

Modelo que controla la ejecución completa del pipeline sintético desde
el endpoint `POST /api/pipeline/run`.

::: backend.api.models.pipeline.PipelineRequest
    options:
      show_root_full_path: false