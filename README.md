# ord-people-fs

Monorepo for the ord-people project.

- `backend/` — FastAPI service (see `backend/README.md`)
- `frontend/` — React/Vite SPA (see `frontend/README.md`)
- `gateway/` — nginx reverse proxy + SPA host

Three Docker images, two compose files. Gateway terminates HTTP/HTTPS, serves the SPA from a shared volume, and proxies `/api/` to the backend.

```
                                  ┌─────────────────┐
                                  │  gateway (nginx)│
   ord-people.ru     ───── 443 ──▶│  serves SPA /   │
   app.ord-people.ru ───── 443 ──▶│  proxies /api/  │──┐
                                  └────────┬────────┘  │
                                  ro mount │           │
                                ┌──────────▼─────┐     │
                                │   spa_dist     │     │
                                │ (named volume) │     │
                                └──────────▲─────┘     │
                                           │ writes    │
                       ┌──────────┐    on  │ start     ▼
                       │ frontend │────────┘     ┌────────────┐
                       │  (init)  │              │  backend   │
                       └──────────┘              │ (FastAPI)  │
                                                 └──┬──────┬──┘
                                                    │      │
                                              ┌─────▼──┐ ┌─▼──────┐
                                              │postgres│ │ redis  │
                                              └────────┘ └────────┘
```

---

## Local development

### Prerequisites

- Docker Engine 24+ with Docker Compose v2
- Free ports `8000` (gateway), `8001` (backend, exposed for direct debugging), `5433` (postgres), `6380` (redis)

### First-time setup

```bash
cp .env.example .env
# The dev compose hard-codes most overrides, but a few backend secrets
# (S3 access keys, etc.) still come from .env — fill them in or leave the
# placeholders and any feature touching S3 will simply fail until you do.
```

### Run

```bash
docker compose -f docker-compose.dev.yml up --build
```

Add `-d` to detach. The first build pulls Node, Python, Postgres and Redis images and runs `npm ci` + `uv sync` — expect a few minutes.

Once everything is up:

| URL                            | What it is                                              |
| ------------------------------ | ------------------------------------------------------- |
| http://localhost:8000/         | SPA (served by gateway from the shared volume)          |
| http://localhost:8000/api/v1/  | API, proxied to backend                                 |
| http://localhost:8000/ht       | Backend healthcheck, proxied                            |
| http://localhost:8001/         | Backend directly (bypasses gateway — handy for cURL)    |
| postgres://postgres:postgres@localhost:5433/ord | Postgres                              |
| redis://localhost:6380         | Redis                                                   |

### Common loops

```bash
# tail logs for one service
docker compose -f docker-compose.dev.yml logs -f backend

# rebuild only the frontend (it's an init container — it exits 0 after publishing)
docker compose -f docker-compose.dev.yml up -d --build frontend
# then restart the gateway so it serves the freshly-published files
docker compose -f docker-compose.dev.yml restart gateway

# rerun alembic migrations (the entrypoint does this on every backend start)
docker compose -f docker-compose.dev.yml restart backend

# wipe the database / redis / SPA bundle and start clean
docker compose -f docker-compose.dev.yml down -v
```

### Frontend hot-reload mode (outside Docker)

The dockerised frontend is a *build* container — it doesn't serve HMR. For interactive frontend work, run Vite on the host against the dockerised backend:

```bash
docker compose -f docker-compose.dev.yml up -d backend postgres redis
cd frontend
npm install
npm run dev   # http://localhost:5173, Vite proxies /api → http://localhost:8001
```

(`frontend/vite.config.ts` reads `VITE_DEV_API_PROXY_TARGET`; default is `http://localhost:8000` but the backend is also exposed on `8001`.)

### Backend tests (host)

```bash
cd backend
uv sync
uv run pytest
uv run ruff check .
uv run pyright
```

---

## Production deployment

Prod runs via `docker-compose.prod.yml` on a VPS. Images come from Docker Hub; the GitHub Actions workflow at `.github/workflows/deploy.yml` builds and pushes them on every push to `main`, then SSHes into the VPS to compose them.

### How a deploy works (in order)

1. `backend-tests` — `ruff` / `pyright` / `pytest` against `backend/`. Blocks the rest on failure.
2. `build-backend`, `build-frontend`, `build-gateway` — parallel Docker builds, pushed to Docker Hub as `${DOCKER_USERNAME}/ord-people-{backend,frontend,gateway}:latest`. The frontend build is consumes `VITE_API_BASE_URL` / `VITE_MEDIA_BASE_URL` as build-args (baked into the bundle).
3. `deploy` —
   - `scp docker-compose.prod.yml` → `/opt/ord-people/` on the VPS.
   - SSH in, write `/opt/ord-people/.env` from GitHub Variables + Secrets (file mode `600`).
   - `docker compose -f docker-compose.prod.yml pull && up -d --remove-orphans`.
   - `docker image prune -af` to reclaim space.
4. `notify` — Telegram message on success or failure.

### One-time VPS / GitHub setup

Before the first push to `main`, set the following up. **Skip any item that's already in place from a previous deploy of the backend-only repo.**

#### 1. GitHub repository **Variables** (Settings → Secrets and variables → Actions → Variables)

New or updated for the monorepo:

| Variable                  | Value                                  |
| ------------------------- | -------------------------------------- |
| `SPA_DOMAIN`              | `ord-people.ru`                        |
| `API_DOMAIN`              | `app.ord-people.ru`                    |
| `VITE_API_BASE_URL`       | `https://app.ord-people.ru/api/v1`     |
| `VITE_MEDIA_BASE_URL`     | the same public URL the backend serves media from (matches `ORD__S3__PUBLIC_URL`) |
| `ORD__APP__DOMAIN`        | `app.ord-people.ru` *(was `backend.ord-people.ru`)* |
| `ORD__APP__ORIGIN_DOMAIN` | `ord-people.ru`                        |

Existing backend variables (preserved unchanged): `ORD__APP__ADMIN_PATH`, `ORD__ADMIN__USERNAME`, `ORD__ADMIN__FIRST_NAME`, `ORD__ADMIN__LAST_NAME`, `ORD__POSTGRES__USER`, `ORD__POSTGRES__DB`, `ORD__POSTGRES__PORT`, `ORD__REDIS__PORT`, `ORD__S3__ENDPOINT_URL`, `ORD__S3__BUCKET_NAME`, `ORD__S3__PUBLIC_URL`, `ORD__LOG__LEVEL`, `ORD__LOG__JSON_LOGS`, `ORD__LOG__TO_FILE`, `GUNICORN_WORKERS`, `BACKEND_MEMORY_LIMIT`, `BACKEND_MEMORY_RESERVE`, `POSTGRES_MEMORY_LIMIT`, `POSTGRES_MAX_CONNECTIONS`, `POSTGRES_SHARED_BUFFERS`, `POSTGRES_WORK_MEM`, `POSTGRES_MAINTENANCE_WORK_MEM`, `POSTGRES_EFFECTIVE_CACHE_SIZE`, `REDIS_MEMORY_LIMIT`, `REDIS_MAXMEMORY`, `NGINX_MEMORY_LIMIT`.

#### 2. GitHub repository **Secrets**

Preserved: `DOCKER_USERNAME`, `DOCKER_PASSWORD`, `HOST`, `USER`, `SSH_KEY`, `PASSPHRASE`, `PORT`, `TELEGRAM_TO`, `TELEGRAM_TOKEN`, `ORD__APP__SECRET_KEY`, `ORD__ADMIN__PASSWORD`, `ORD__AUTH__PEPPER`, `ORD__POSTGRES__PASSWORD`, `ORD__REDIS__PASSWORD`, `ORD__S3__ACCESS_KEY`, `ORD__S3__SECRET_KEY`.

**Remove** (no longer used — frontend S3 deploy is gone): `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`.

#### 3. DNS

Both `ord-people.ru` and `app.ord-people.ru` must resolve to the VPS IP. `A` (and `AAAA` if you have IPv6) records.

#### 4. Let's Encrypt certificates on the VPS

The prod nginx config expects certs at `/etc/letsencrypt/live/${SPA_DOMAIN}/` and `/etc/letsencrypt/live/${API_DOMAIN}/`. If the host previously served `backend.ord-people.ru`, that cert won't match the new API domain — issue both fresh:

```bash
# Open port 80 briefly for the HTTP-01 challenge if nothing is bound there yet.
sudo certbot certonly --webroot -w /var/www/certbot -d ord-people.ru
sudo certbot certonly --webroot -w /var/www/certbot -d app.ord-people.ru
```

If certbot's webroot path doesn't exist yet: `sudo mkdir -p /var/www/certbot`.

Renewal: the existing certbot timer renews in place. The gateway only reads the certs at start (and `nginx reload` time), so a `docker compose restart gateway` is enough after a renewal — or use a deploy-hook.

#### 5. VPS filesystem layout

```bash
# On the VPS, as root:
sudo mkdir -p /opt/ord-people /var/log/ord-people /var/log/nginx /var/www/certbot
sudo chown -R "$USER":"$USER" /opt/ord-people
```

The deploy job writes `docker-compose.prod.yml` and `.env` (mode 600) into `/opt/ord-people/` and runs compose from there. If you previously deployed to `/opt/ord-people-backend` or `/opt/ord-people-frontend`, those dirs can be removed after the first successful deploy of the new layout — but bring the new stack up first.

#### 6. Old S3 SPA bucket

After the first successful deploy, the SPA is served from the gateway and the S3 bucket that previously held it is no longer read by anyone. Empty/delete it whenever convenient.

### Manual deploy (no GitHub Actions)

Useful for bootstrapping or recovery.

```bash
# 1. From your laptop, copy the compose file:
scp docker-compose.prod.yml user@host:/opt/ord-people/

# 2. SSH in and write /opt/ord-people/.env by hand. Use .env.example as the template,
#    point the *_IMAGE vars at the images currently on Docker Hub
#    (e.g. BACKEND_IMAGE=youruser/ord-people-backend:latest).
ssh user@host
cd /opt/ord-people
chmod 600 .env

# 3. Pull and bring up:
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d --remove-orphans

# 4. Tail logs to confirm:
docker compose -f docker-compose.prod.yml logs -f
```

### Rollback

The deploy is image-based, so rollback = pin to a previous tag.

```bash
# On the VPS:
cd /opt/ord-people

# 1. Find a previous image digest:
docker images --digests 'youruser/ord-people-backend' | head

# 2. Edit .env, replace BACKEND_IMAGE (and/or FRONTEND_IMAGE / GATEWAY_IMAGE) with
#    the digest form, e.g.
#    BACKEND_IMAGE=youruser/ord-people-backend@sha256:abc123...

# 3. Re-up:
docker compose -f docker-compose.prod.yml up -d
```

(Currently the workflow only pushes `:latest`. If you want point-in-time tags for easy rollback, the simplest change is to also tag with `${{ github.sha }}` in each build job and surface that as the deploy's `*_IMAGE` value — open an issue / send a PR.)

### Observability

- **App logs**: `docker compose -f docker-compose.prod.yml logs -f <service>`. Json-file driver with rotation: `max-size: 100m`, `max-file: 10` (per service).
- **Nginx access/error logs**: bind-mounted from container `/var/log/nginx` → host `/var/log/nginx`.
- **Backend file logs**: bind-mounted from container `/var/log/ord-people` → host `/var/log/ord-people` (enabled only when `ORD__LOG__TO_FILE=true`).
- **Healthchecks**: gateway → `docker inspect ord_people_backend` to see backend health status; backend exposes `/ht`.

### Resource limits

Set per service via the `*_MEMORY_LIMIT` vars in `.env`. Postgres tuning comes from `POSTGRES_*` env vars and is applied via `command:` overrides in `docker-compose.prod.yml`. Defaults in `.env.example` target a small (~1-2 GB RAM) VPS.

---

## Service isolation guarantees

Each image contains *only* its own files. This is verified at build time by `.dockerignore` deny-lists and tested by the dev-stack verification step:

- `backend/` image: FastAPI app + venv. No `node_modules`, no `vite.config.ts`, no nginx configs.
- `frontend/` image: bare alpine + `/dist/` (the Vite output). No source, no `node_modules`, no `package.json`. ~14 MB.
- `gateway/` image: nginx + two `.conf.template` files at `/etc/gateway/` + a render entrypoint. No backend or frontend source.

Inter-service communication only via: the bridge network (gateway ↔ backend), the named `spa_dist` volume (frontend → gateway, read-only on gateway side), and the host-mounted `/etc/letsencrypt` (prod gateway only, read-only).
