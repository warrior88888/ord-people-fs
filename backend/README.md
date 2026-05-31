# ord-people

FastAPI backend for **ord-people.ru**.

Stack: Python 3.14 · FastAPI · SQLAlchemy + asyncpg · PostgreSQL 17 · Redis 8 · Gunicorn/Uvicorn · S3-compatible storage · nginx · Docker.

---

## Table of contents

- [Requirements](#requirements)
- [Configuration](#configuration)
- [Local dev (no Docker)](#local-dev-no-docker)
- [Docker dev](#docker-dev)
- [Production](#production)
- [CI/CD](#cicd)
- [Useful commands](#useful-commands)

---

## Requirements

| Tool | Version |
|------|---------|
| Python | 3.14+ |
| [uv](https://docs.astral.sh/uv/) | latest |
| Docker + Compose | 24+ |
| PostgreSQL | 17 (only for local-dev without Docker) |
| Redis | 8 (only for local-dev without Docker) |

---

## Configuration

All settings are loaded by `pydantic-settings` from environment variables and/or a `.env` file in the repo root.

- **Prefix:** `ORD__`
- **Nested delimiter:** `__`
- Example: `ORD__POSTGRES__PASSWORD=...` → `settings.postgres.password`.

Required variables (no defaults):

```
ORD__ADMIN__USERNAME
ORD__ADMIN__PASSWORD
ORD__ADMIN__FIRST_NAME
ORD__ADMIN__LAST_NAME
ORD__AUTH__PEPPER
ORD__POSTGRES__PASSWORD
ORD__S3__ACCESS_KEY
ORD__S3__SECRET_KEY
ORD__S3__ENDPOINT_URL
ORD__S3__BUCKET_NAME
ORD__S3__PUBLIC_URL
```

Common optional variables:

```
ORD__APP__DEBUG=false
ORD__APP__SECRET_KEY=change-me
ORD__APP__DOMAIN=backend.ord-people.ru
ORD__APP__ORIGIN_DOMAIN=ord-people.ru
ORD__APP__COOKIE_SECURE=true
ORD__APP__BEHIND_PROXY=true
ORD__APP__FORWARDED_ALLOW_IPS=*
ORD__POSTGRES__HOST=localhost
ORD__POSTGRES__PORT=5432
ORD__POSTGRES__DB=ord
ORD__POSTGRES__USER=postgres
ORD__REDIS__HOST=localhost
ORD__REDIS__PORT=6379
ORD__REDIS__PASSWORD=
ORD__LOG__LEVEL=INFO
ORD__LOG__JSON_LOGS=false
ORD__LOG__TO_FILE=false
GUNICORN_WORKERS=3
FORWARDED_ALLOW_IPS=127.0.0.1
```

---

## Local dev (no Docker)

Best for fast iteration with hot reload.

### 1. Install deps

```bash
uv sync
```

### 2. Start infrastructure

You still need Postgres + Redis. Easiest way — reuse the dev compose for just those services:

```bash
docker compose -f docker-compose.dev.yml up -d postgres redis
```

Postgres will be on `localhost:5433`, Redis on `localhost:6380`.

S3 is not run locally — point `ORD__S3__*` to a real bucket (used by frontend dev too).

### 3. Create `.env`

```env
ORD__APP__DEBUG=true
ORD__APP__COOKIE_SECURE=false
ORD__APP__SECRET_KEY=dev-secret
ORD__ADMIN__USERNAME=admin
ORD__ADMIN__PASSWORD=admin
ORD__ADMIN__FIRST_NAME=Admin
ORD__ADMIN__LAST_NAME=Root
ORD__AUTH__PEPPER=dev-pepper
ORD__POSTGRES__HOST=localhost
ORD__POSTGRES__PORT=5433
ORD__POSTGRES__DB=ord
ORD__POSTGRES__USER=postgres
ORD__POSTGRES__PASSWORD=postgres
ORD__REDIS__HOST=localhost
ORD__REDIS__PORT=6380
ORD__S3__ACCESS_KEY=<real-key>
ORD__S3__SECRET_KEY=<real-secret>
ORD__S3__ENDPOINT_URL=https://storage.yandexcloud.net
ORD__S3__BUCKET_NAME=ord-people
ORD__S3__PUBLIC_URL=https://ord-people.storage.yandexcloud.net
```

### 4. Run migrations

```bash
uv run alembic upgrade head
```

> In Docker the app applies migrations automatically via its entrypoint (`alembic upgrade head` before `gunicorn`). For local-dev (step above) you run it manually since the app starts via `fastapi dev`.

### 5. Start the app

```bash
uv run fastapi dev src/ord_people/main.py
```

App: <http://localhost:8000> · Docs: <http://localhost:8000/docs> · Health: <http://localhost:8000/ht>

---

## Docker dev

Full stack in containers — Postgres, Redis, backend, nginx. Ports exposed for monitoring.

### Start

```bash
docker compose -f docker-compose.dev.yml up --build -d
```

| Service  | Host port | Notes |
|----------|-----------|-------|
| nginx    | `8000`    | entrypoint → backend |
| backend  | `8001`    | direct access, bypassing nginx |
| postgres | `5433`    | `postgres / postgres / ord` |
| redis    | `6380`    | no password |

> S3 is not run locally. `ORD__S3__*` is read from `.env` — point it at the real bucket (shared with the frontend during dev).

### Migrations

Applied automatically on backend startup by the image entrypoint (`alembic upgrade head` runs before `gunicorn`). No separate `migrate` container or manual command needed.

To run ad-hoc:

```bash
docker compose -f docker-compose.dev.yml exec backend alembic upgrade head
```

### Logs / shell

```bash
docker compose -f docker-compose.dev.yml logs -f backend
docker compose -f docker-compose.dev.yml exec backend bash
```

### Stop

```bash
docker compose -f docker-compose.dev.yml down          # keep data
docker compose -f docker-compose.dev.yml down -v       # wipe volumes
```

> Most `ORD__*` env vars are hard-coded in `docker-compose.dev.yml`. `.env` is still required for the S3 credentials (`ORD__S3__*`).

---

## Production

Deployed to a VPS via GitHub Actions.

**Architecture / DNS:**

| Domain                  | Hosting                        | Role                                   |
|-------------------------|--------------------------------|----------------------------------------|
| `ord-people.ru`         | S3 bucket (static)             | Frontend SPA (origin)                  |
| `www.ord-people.ru`     | S3 bucket (static)             | Frontend SPA                           |
| `media.ord-people.ru`   | S3 bucket                      | Media (uploaded images, etc.)          |
| `backend.ord-people.ru` | This VPS → nginx → FastAPI     | Backend API — only the SPA talks to it |

The backend nginx only serves `backend.ord-people.ru`; any request with a different `Host` header (apex, www, IP scans) gets `444`. CORS allows only `https://ord-people.ru` and `https://www.ord-people.ru` (driven by `ORD__APP__ORIGIN_DOMAIN`).

Host filesystem layout:

```
/opt/ord-people/
├── docker-compose.prod.yml
├── nginx/nginx.prod.conf
└── .env                       # written by CI, chmod 600
/etc/letsencrypt/              # certbot certs (mounted into nginx)
/var/www/certbot/              # ACME http-01 challenge
/var/log/ord-people/           # backend logs
/var/log/nginx/                # nginx logs
```

### 1. Bootstrap the VPS (one-time)

```bash
apt update && apt install -y docker.io docker-compose-plugin certbot
mkdir -p /opt/ord-people /var/log/ord-people /var/www/certbot
```

### 2. Issue TLS certificate

```bash
certbot certonly --standalone \
  -d backend.ord-people.ru \
  --email you@example.com --agree-tos --no-eff-email
```

> The apex and `www.ord-people.ru` certificates live with the S3/CDN provider hosting the frontend — this nginx only needs `backend.ord-people.ru`.

Schedule auto-renewal (already done by certbot on Debian/Ubuntu via systemd timer).

### 3. Configure GitHub

**Secrets** (Settings → Secrets and variables → Actions → Secrets):

| Secret | Purpose |
|--------|---------|
| `DOCKER_USERNAME` / `DOCKER_PASSWORD` | DockerHub login |
| `HOST` / `USER` / `PORT` / `SSH_KEY` / `PASSPHRASE` | SSH to VPS |
| `TELEGRAM_TO` / `TELEGRAM_TOKEN` | deploy notifications |
| `ORD__APP__SECRET_KEY` | session/CSRF key |
| `ORD__ADMIN__PASSWORD` | initial admin password |
| `ORD__AUTH__PEPPER` | password hashing pepper |
| `ORD__POSTGRES__PASSWORD` | DB password |
| `ORD__REDIS__PASSWORD` | Redis password |
| `ORD__S3__ACCESS_KEY` / `ORD__S3__SECRET_KEY` | S3 credentials |

**Repository variables** (Settings → Secrets and variables → Actions → Variables):

| Variable | Example |
|----------|---------|
| `ORD__APP__DOMAIN` | `backend.ord-people.ru` |
| `ORD__APP__ORIGIN_DOMAIN` | `ord-people.ru` |
| `ORD__APP__ADMIN_PATH` | `admin` |
| `ORD__ADMIN__USERNAME` | `admin` |
| `ORD__ADMIN__FIRST_NAME` | `Admin` |
| `ORD__ADMIN__LAST_NAME` | `Root` |
| `ORD__POSTGRES__USER` | `ord` |
| `ORD__POSTGRES__DB` | `ord` |
| `ORD__POSTGRES__PORT` | `5432` |
| `ORD__REDIS__PORT` | `6379` |
| `ORD__S3__ENDPOINT_URL` | `https://storage.yandexcloud.net` |
| `ORD__S3__BUCKET_NAME` | `ord-people` |
| `ORD__S3__PUBLIC_URL` | `https://ord-people.storage.yandexcloud.net` |
| `ORD__LOG__LEVEL` | `INFO` |
| `ORD__LOG__JSON_LOGS` | `true` |
| `ORD__LOG__TO_FILE` | `true` |
| `GUNICORN_WORKERS` | `3` |
| `BACKEND_MEMORY_LIMIT` / `BACKEND_MEMORY_RESERVE` | `512M` / `256M` |
| `POSTGRES_MEMORY_LIMIT` | `512M` |
| `POSTGRES_MAX_CONNECTIONS` | `20` |
| `POSTGRES_SHARED_BUFFERS` | `128MB` |
| `POSTGRES_WORK_MEM` | `4MB` |
| `POSTGRES_MAINTENANCE_WORK_MEM` | `32MB` |
| `POSTGRES_EFFECTIVE_CACHE_SIZE` | `384MB` |
| `REDIS_MEMORY_LIMIT` / `REDIS_MAXMEMORY` | `128M` / `128mb` |
| `NGINX_MEMORY_LIMIT` | `128M` |

### 4. Deploy

```bash
git push origin main
```

GitHub Actions will: run tests → build & push image → SCP configs to VPS → write `.env` → `docker compose pull && up -d` → Telegram notification.

### 5. Manual deploy (fallback)

```bash
ssh vps
cd /opt/ord-people
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d --remove-orphans
# migrations run automatically via the backend entrypoint
```

### Security highlights (prod)

- nginx forces HTTPS, TLS 1.2/1.3 only, HSTS, frame-deny, COOP, Permissions-Policy
- only `backend.ord-people.ru` is served — default server returns `444` on any other `Host`
- `/ht` healthcheck is restricted to private/loopback ranges (`127.0.0.1`, `10/8`, `172.16/12`, `192.168/16`) — internet clients get `403`
- per-IP rate limiting (10 r/s, burst 20) and connection limiting (20/IP) on `/api/`
- request method whitelist, scanner UA blacklist, dotfile / wp- / config-extension traps return 444
- Postgres and Redis on `internal: true` networks — only the backend can reach them
- memory limits on every container, Postgres tuned via `command`
- `.env` written `chmod 600`, image runs as non-root user `ord`

---

## CI/CD

Workflow: [`.github/workflows/main.yaml`](.github/workflows/main.yaml).

Jobs run on push to `main`:

1. **tests** — `ruff`, `pyright`, `pytest` with 90% coverage gate. Redis is provided as a GitHub service.
2. **build-and-push** — multi-stage build via `Dockerfile`, push `:latest` to DockerHub with GHA cache.
3. **deploy** — SCP compose+nginx to VPS, render `.env` from secrets/variables, `docker compose up -d`.
4. **notify** — Telegram on success/failure.

---

## Useful commands

```bash
# Tests + coverage
uv run pytest --cov=src/ord_people --cov-branch --cov-report=term-missing

# Lint & format
uv run ruff check . --fix
uv run ruff format .

# Type-check
uv run pyright

# Alembic
uv run alembic revision --autogenerate -m "message"
uv run alembic upgrade head
uv run alembic downgrade -1
```
