# Operaciones en Producción

Runbook para el servidor de producción en Contabo VPS (`b2b-graph-intelligence.duckdns.org`).

---

## Monitorización

### Estado de contenedores

```bash
docker compose ps
# Todos deben estar "healthy" o "Up"
```

### Logs en tiempo real

```bash
# API backend
docker compose logs backend --tail=50 -f

# Neo4j (filtrado a errores)
docker compose logs neo4j --tail=20 -f

# Nginx (acceso + errores)
docker compose logs nginx --tail=30 -f
```

### Uso de memoria Neo4j

```bash
docker stats neo4j --no-stream
# Columns: MEM USAGE / LIMIT, MEM %
# Objetivo: mantenerse por debajo del 80 % del límite configurado
```

### Health check manual

```bash
curl -s https://b2b-graph-intelligence.duckdns.org/api/health | python3 -m json.tool
# Esperado: {"status": "ok", "neo4j": "connected"}
```

---

## Copia de seguridad de la base de datos

Hacer backup **antes** de ejecutar `main_cli.py analyze` o `main_cli.py all`.

```bash
# 1. Crear directorio de backup
mkdir -p /root/backups

# 2. Dump de Neo4j (en caliente con Neo4j 5.x)
docker exec neo4j neo4j-admin database dump neo4j \
  --to-path=/backup \
  --overwrite-destination=true

# 3. Copiar del contenedor al host
docker cp neo4j:/backup/neo4j.dump /root/backups/neo4j_$(date +%Y%m%d_%H%M%S).dump

# 4. Verificar tamaño del fichero
ls -lh /root/backups/
```

### Restaurar un backup

```bash
# Parar la API (evita escrituras durante la restauración)
docker compose stop backend

# Restaurar el dump
docker exec -it neo4j neo4j-admin database load neo4j \
  --from-path=/backup \
  --overwrite-destination=true

docker compose start backend
```

---

## Renovación de certificado SSL

El crontab automático renueva el certificado el día 1 de cada mes a las 03:00.
Si falla, renovar manualmente:

```bash
# 1. Parar nginx (libera el puerto 80)
docker compose stop nginx

# 2. Renovar
certbot renew \
  --config-dir /root/TFG-B2B/certbot/certs \
  --work-dir /tmp/certbot \
  --logs-dir /tmp/certbot-logs

# 3. Reiniciar nginx
docker compose start nginx

# 4. Verificar expiración
openssl s_client -connect b2b-graph-intelligence.duckdns.org:443 -servername b2b-graph-intelligence.duckdns.org \
  </dev/null 2>/dev/null | openssl x509 -noout -dates
```

**Error común:** `CERTIFICATE_VERIFY_FAILED` tras renovación → el contenedor nginx
tiene el certificado anterior cacheado. Solución: `docker compose restart nginx`.

---

## Ajustar memoria de Neo4j

Editar las variables de entorno en `docker-compose.yml`:

```yaml
environment:
  NEO4J_server_memory_heap_initial__size: "1G"
  NEO4J_server_memory_heap_max__size:     "4G"
  NEO4J_server_memory_pagecache__size:    "2G"
```

| Variable | Descripción | Recomendado (12 GB RAM) |
|---|---|---|
| `heap_initial__size` | Heap inicial de la JVM | `1G` |
| `heap_max__size` | Heap máximo de la JVM | `4G` |
| `pagecache__size` | Caché de páginas del grafo | `2G` |

Tras cambiar: `docker compose up -d neo4j` (reinicia solo ese servicio).

---

## Re-seeding de usuarios

Necesario tras un wipe completo de la base de datos (`docker compose down -v`):

```bash
# Regenerar usuarios demo en SQLite
python backend/main_cli.py seed

# Usuarios creados:
# - admin@demo.com      / password: admin1234    (role: admin)
# - company1@demo.com   / password: company1234  (role: company_user)
# - company2@demo.com   / ...
# - company{N}@demo.com / ...
```

---

## Variables de entorno — referencia completa

Fichero: `/root/TFG-B2B/.env`

| Variable | Descripción | Valor por defecto |
|---|---|---|
| `NEO4J_URI` | URI Bolt del servidor Neo4j | `bolt://neo4j:7687` (Docker) |
| `NEO4J_USER` | Usuario Neo4j | `neo4j` |
| `NEO4J_PASSWORD` | Contraseña Neo4j | `AdminUser1234` |
| `NEO4J_DATABASE` | Base de datos activa | `neo4j` |
| `JWT_SECRET_KEY` | Secreto HMAC-SHA256 para firmar tokens | **Cambiar en producción** |
| `JWT_ALGORITHM` | Algoritmo JWT | `HS256` |
| `JWT_EXPIRE_MINUTES` | Vida del token en minutos | `1440` (24 h) |
| `PUBLIC_URL` | URL pública del sitio (para CORS) | `https://b2b-graph-intelligence.duckdns.org` |
| `NEXT_PUBLIC_API_URL` | URL base de la API (frontend) | `https://b2b-graph-intelligence.duckdns.org` |

---

## Rollback de la aplicación

Si un despliegue introduce una regresión:

```bash
# 1. Ver historial de commits
git log --oneline -10

# 2. Identificar el commit estable anterior
# 3. Revertir (crea un nuevo commit de reversión)
git revert <commit-hash>
git push origin main

# 4. El workflow de CD redespliega automáticamente en ~2 min
# (sin tiempo de inactividad — Compose solo reinicia el contenedor cambiado)
```

Para un rollback urgente sin esperar CD:

```bash
git reset --hard <commit-hash-estable>
docker compose up -d --build backend frontend
```

---

## Escalar el pipeline para grafos grandes

Si la generación de >1000 empresas consume demasiada RAM:

```bash
# Reducir batch size del cargador
python backend/main_cli.py load --batch_size_loader 2000

# O ejecutar fases por separado con espera entre ellas
python backend/main_cli.py generate --rows 1000 --seed 42
# (esperar a que Neo4j libere memoria)
python backend/main_cli.py load --batch_size_loader 3000
python backend/main_cli.py analyze
```

Referencia de uso de memoria orientativo:

| Empresas | Documentos aprox. | RAM Neo4j | RAM Python |
|---|---|---|---|
| 300 | ~28 000 | ~1.5 GB | ~400 MB |
| 600 | ~56 000 | ~3 GB | ~700 MB |
| 1000 | ~93 000 | ~5 GB | ~1.1 GB |