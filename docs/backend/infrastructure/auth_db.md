# Capa de Autenticación - Base de Datos

Módulos que gestionan la persistencia relacional de usuarios en SQLite y
el seeding inicial de cuentas demo. Esta capa es independiente de Neo4j ya que
SQLite almacena credenciales mientras que Neo4j almacena el grafo de empresas.

---

## Modelo y motor (`database.py`)

::: backend.auth.db.database.User
    options:
      show_root_full_path: false

::: backend.auth.db.database.get_db
    options:
      show_root_full_path: false

---

## Seeding de usuarios demo (`seed_users.py`)

::: backend.auth.db.seed_users.seed
    options:
      show_root_full_path: false

### Flujo de seeding

```
Neo4j  ──MATCH (c:Company)──▶  lista de empresas
                                      │
                              por cada empresa
                                      │
                              ┌───────▼────────┐
                              │  ¿existe ya    │
                              │  en SQLite?    │
                              └──┬─────────┬───┘
                                Sí         No
                                │           │
                            skipped     INSERT User
                                         company{i}@demo.com
                                         role = company_user
                              └─────────────┘
                                      │
                              ¿existe admin@demo.com?
                                  No → INSERT admin
                                      role = admin
```

| Usuario generado | Contraseña | Rol |
|---|---|---|
| `company0@demo.com` … `companyN@demo.com` | `Demo1234!` | `company_user` |
| `admin@demo.com` | `Demo1234!` | `admin` |