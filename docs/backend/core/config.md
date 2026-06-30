# Core - Configuración y Utilidades

Módulos usados por todas las capas del sistema. No dependen
de Neo4j ni de FastAPI, lo que los hace testeables de forma aislada.

---

## Configuración (`config.py`)

::: backend.core.config.Settings
    options:
      show_root_full_path: false

::: backend.core.config.load_settings
    options:
      show_root_full_path: false

### Variables de entorno

| Variable | Valor por defecto | Descripción |
|---|---|---|
| `NEO4J_URI` | `bolt://localhost:7687` | URI del servidor Neo4j |
| `NEO4J_USER` | `neo4j` | Usuario Neo4j |
| `NEO4J_PASSWORD` | `AdminUser1234` | Contraseña Neo4j |
| `NEO4J_DATABASE` | `neo4j` | Base de datos activa |
| `JWT_SECRET_KEY` | `change-me-in-production` | Clave HMAC para JWT |
| `TFG_SEED` | `None` (aleatorio) | Semilla global del generador |

---

## Utilidades (`utils.py`)

### Exportación

::: backend.core.utils.write_step_artifact
    options:
      show_root_full_path: false

::: backend.core.utils.export_dict_to_json
    options:
      show_root_full_path: false

::: backend.core.utils.export_df_to_json
    options:
      show_root_full_path: false

### Conversión segura

::: backend.core.utils.safe_float
    options:
      show_root_full_path: false

::: backend.core.utils.safe_int
    options:
      show_root_full_path: false

::: backend.core.utils.safe_date
    options:
      show_root_full_path: false

::: backend.core.utils.pick
    options:
      show_root_full_path: false