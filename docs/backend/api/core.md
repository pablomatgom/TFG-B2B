# Núcleo de la API

Módulos que sostienen la aplicación FastAPI: punto de entrada, dependencias
compartidas y helpers de serialización.

---

## Aplicación principal (`main.py`)

Crea la instancia `app` de FastAPI y monta todos los routers en el orden
siguiente:

| Router | Prefijo |
|---|---|
| `auth` | `/auth` |
| `health` | `/`, `/api/health` |
| `dashboard` | `/api/dashboard` |
| `analytics` | `/api/analytics` |
| `pipeline` | `/api/pipeline` |
| `company` | `/api/company`, `/api/documents` |

### CORS

Orígenes permitidos controlados por la variable de entorno `FRONTEND_URL`
(por defecto `http://localhost:3000`).  Todos los métodos y cabeceras están
permitidos con credenciales habilitadas (`allow_credentials=True`).

### Manejador global de excepciones

::: backend.api.main.global_exception_handler
    options:
      show_root_full_path: false

---

## Dependencias (`dependencies.py`)

### Constantes JWT y rutas

| Constante | Valor | Descripción |
|---|---|---|
| `SECRET_KEY` | `settings.jwt_secret_key` | Clave HMAC leída de `Settings` |
| `ALGORITHM` | `"HS256"` | Algoritmo de firma JWT simétrico |
| `EXPIRE_HOURS` | `24` | Vida útil del token en horas |
| `EXPORT_DIR` | `settings.data_export_dir` | Directorio de JSONs pre-computados |

### Dependencias FastAPI

::: backend.api.dependencies.get_analyzer_instance
    options:
      show_root_full_path: false

::: backend.api.dependencies.get_current_user
    options:
      show_root_full_path: false

### Helpers de serialización

::: backend.api.dependencies.read_json
    options:
      show_root_full_path: false

::: backend.api.dependencies.neo4j_to_dict
    options:
      show_root_full_path: false