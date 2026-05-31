# Monorepo Restructure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Merge the existing `ord-people/` (FastAPI backend, currently owns nginx + compose) and `ord-people-frontend/` (React/Vite SPA, currently deployed to S3) into a single monorepo at the repo root with three isolated services — `backend/`, `frontend/`, `gateway/` — orchestrated by `docker-compose.dev.yml` / `docker-compose.prod.yml`, served behind a single nginx gateway with SSL on two domains.

**Architecture:**
- `gateway/` — standalone nginx image (built from `gateway/Dockerfile`). Serves SPA static files at `ord-people.ru` from a shared `spa_dist` volume (read-only) and reverse-proxies `app.ord-people.ru/api/` to `backend:8000`. Holds SSL termination via `/etc/letsencrypt` bind-mount in prod.
- `frontend/` — multi-stage Dockerfile. Stage 1 = `node:22-alpine` running `npm ci && npm run build`. Stage 2 = `alpine` containing only `/dist`. The container's entrypoint copies `/dist/*` into the shared `spa_dist` volume and exits (0). Gateway depends on its successful completion.
- `backend/` — existing FastAPI image, unchanged internally. Only the Docker build context path changes (root → `./backend`).
- `.env` at repo root is the single source of truth. All backend `ORD__*` variable names preserved exactly. New gateway/frontend vars follow existing conventions (UPPER_SNAKE_CASE, no `ORD__` prefix unless backend-owned).
- One GitHub Actions workflow at repo root replaces both prior workflows. Path filters skip jobs whose source didn't change.

**Tech Stack:** Docker / Docker Compose v2, nginx 1.31-alpine, Python 3.14 + uv (backend), Node 22 + Vite 6 (frontend), GitHub Actions, Let's Encrypt (existing certs already on the VPS).

---

## File Structure

After this plan executes, the repo will look like:

```
ord-people-fs/                          # repo root (current cwd; currently has two sibling repos and .DS_Store / .idea)
├── .env                                 # local-only; gitignored; copy of .env.example with real secrets
├── .env.example                         # single source of truth for ALL env vars (backend + frontend + gateway + infra)
├── .gitignore                           # merged from both repos
├── docker-compose.dev.yml               # local dev: postgres, redis, backend, frontend (build & exit), gateway
├── docker-compose.prod.yml              # prod: same services + SSL volumes + mem limits + image refs
├── README.md                            # short pointer to backend/ and frontend/ READMEs
├── .github/
│   └── workflows/
│       └── deploy.yml                   # single CI/CD pipeline (replaces backend's main.yaml + frontend's deploy.yml)
├── backend/                             # = current ord-people/ (moved as-is)
│   ├── Dockerfile                       # unchanged
│   ├── .dockerignore                    # unchanged
│   ├── docker-entrypoint.sh             # unchanged
│   ├── pyproject.toml                   # unchanged
│   ├── uv.lock                          # unchanged
│   ├── alembic.ini                      # unchanged
│   ├── gunicorn.conf.py                 # unchanged
│   ├── migrations/                      # unchanged
│   ├── src/ord_people/                  # unchanged
│   ├── tests/                           # unchanged
│   └── README.md                        # unchanged (still describes backend only)
├── frontend/                            # = current ord-people-frontend/ (moved as-is) + new Dockerfile
│   ├── Dockerfile                       # NEW: multi-stage; final stage = alpine with /dist + copy-to-volume entrypoint
│   ├── .dockerignore                    # NEW: excludes node_modules, .env*, dist, .git, .idea, etc.
│   ├── package.json                     # unchanged
│   ├── package-lock.json                # unchanged
│   ├── vite.config.ts                   # unchanged
│   ├── tsconfig*.json                   # unchanged
│   ├── eslint.config.js                 # unchanged
│   ├── index.html                       # unchanged
│   ├── public/                          # unchanged
│   ├── src/                             # unchanged
│   ├── openapi.json                     # unchanged
│   └── README.md                        # unchanged
└── gateway/
    ├── Dockerfile                       # NEW: FROM nginx:1.31.1-alpine3.23-slim; COPY only conf templates + entrypoint
    ├── .dockerignore                    # NEW: deny-list everything except the two confs + entrypoint
    ├── docker-entrypoint.sh             # NEW: envsubst ${SPA_DOMAIN} ${API_DOMAIN} into final conf, then exec nginx
    ├── nginx.dev.conf.template          # NEW: serves SPA at /, proxies /api → backend, no SSL
    └── nginx.prod.conf.template         # NEW: SSL + two server blocks (SPA_DOMAIN, API_DOMAIN), all current security rules preserved
```

Files **deleted** from the old layout after the move:
- `ord-people/nginx/` (moved → `gateway/`, rewritten as templates)
- `ord-people/docker-compose.dev.yml` and `docker-compose.prod.yml` (replaced at root)
- `ord-people/.env` (moved → root `.env`; gitignored)
- `ord-people/.github/workflows/main.yaml` (replaced)
- `ord-people-frontend/.github/workflows/deploy.yml` (replaced)
- `ord-people-frontend/.env.example`, `.env.local` (merged into root `.env.example`)
- Eventually the empty `ord-people/` and `ord-people-frontend/` directories themselves.

---

## Pre-flight: capture the current state

The current working directory `/Users/alexey/projects/ord-people-fs` is **not yet a git repo** (the two child dirs `ord-people/` and `ord-people-frontend/` are each their own repos). Before any restructuring we initialise a single repo at the root and commit a snapshot so every later step is reversible.

### Task 0: Initialise the monorepo git history

**Files:**
- Create: `/Users/alexey/projects/ord-people-fs/.gitignore`
- Create: `/Users/alexey/projects/ord-people-fs/README.md` (minimal stub)

- [ ] **Step 1: Verify current state**

Run:
```bash
cd /Users/alexey/projects/ord-people-fs
ls -la
git rev-parse --is-inside-work-tree 2>&1 || echo "not a repo (expected)"
```

Expected: `not a repo (expected)`. Two sibling dirs `ord-people/` and `ord-people-frontend/` present.

- [ ] **Step 2: Write a top-level `.gitignore`** (merged from both child repos, plus IDE/OS noise that was floating at the root):

```gitignore
# OS
.DS_Store

# IDE
.idea/
*.iml

# Python
__pycache__/
*.py[cod]
*$py.class
*.egg-info/
.venv/
.pytest_cache/
.ruff_cache/
.mypy_cache/
.coverage
.coverage.*
htmlcov/

# Node
node_modules/
dist/
dist-ssr/
*.tsbuildinfo
.vite/
*.local

# Environment files - never commit, see .env.example
.env
.env.*
!.env.example

# Logs
*.log

# Claude
.claude/

# Playwright
.playwright-mcp/
```

- [ ] **Step 3: Write a stub `README.md`**:

```markdown
# ord-people-fs

Monorepo for the ord-people project.

- `backend/` — FastAPI service (see `backend/README.md`)
- `frontend/` — React/Vite SPA (see `frontend/README.md`)
- `gateway/` — nginx reverse proxy + SPA host

Local development: `docker compose -f docker-compose.dev.yml up --build`.
```

- [ ] **Step 4: Initialise repo and capture the pre-restructure snapshot**

Run:
```bash
cd /Users/alexey/projects/ord-people-fs
git init -b main
# Stage everything except things matched by the new .gitignore.
# We do NOT want the child .git/ dirs to become submodules — strip them first.
rm -rf ord-people/.git ord-people-frontend/.git
git add .
git status --short | head -20
git commit -m "chore: import backend and frontend repos as-is before restructure"
```

Expected: a single commit containing `ord-people/`, `ord-people-frontend/`, `.gitignore`, `README.md`. No `.git` subdirs inside the children.

> ⚠️ The child repos' git history is intentionally discarded here. If preserving it matters, ask the user before running this step and use `git subtree add` instead.

---

## Phase 1 — Move files into the new layout

These tasks are pure renames. No content edits yet. The build is *intentionally* broken between Task 1 and the end of Phase 2 — we're moving files to their new homes first, then patching paths.

### Task 1: Rename `ord-people/` → `backend/`

**Files:**
- Rename: `ord-people/` → `backend/`

- [ ] **Step 1: Use `git mv` so history follows the rename**

Run:
```bash
cd /Users/alexey/projects/ord-people-fs
git mv ord-people backend
ls backend/ | head
```

Expected: `Dockerfile`, `pyproject.toml`, `src/`, `tests/`, `nginx/`, `docker-compose.dev.yml`, `docker-compose.prod.yml`, `.env`, etc. all present under `backend/`.

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "refactor: rename ord-people -> backend"
```

### Task 2: Rename `ord-people-frontend/` → `frontend/`

**Files:**
- Rename: `ord-people-frontend/` → `frontend/`

- [ ] **Step 1: Move**

Run:
```bash
cd /Users/alexey/projects/ord-people-fs
git mv ord-people-frontend frontend
ls frontend/ | head
```

Expected: `package.json`, `src/`, `public/`, `vite.config.ts`, `index.html`, `.env.example`, `.env.local`, etc.

- [ ] **Step 2: Drop `node_modules/` if it was committed by accident** (the child's `.gitignore` already excluded it, but the move-by-rename in Task 0 captured whatever was on disk — defensively re-check)

Run:
```bash
git ls-files frontend/node_modules | head
```

If output is non-empty:
```bash
git rm -r --cached frontend/node_modules
```

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "refactor: rename ord-people-frontend -> frontend"
```

### Task 3: Promote the backend's `.env` to repo root and remove from backend/

**Files:**
- Move: `backend/.env` → `.env`
- Move: `backend/.env`-related expectations stay (compose at root will read `./.env`)

- [ ] **Step 1: Verify the file isn't tracked (`.env` is gitignored)**

Run:
```bash
git ls-files backend/.env
```

Expected: empty output (gitignored). If non-empty, stop and untrack: `git rm --cached backend/.env`.

- [ ] **Step 2: Physically move and verify**

Run:
```bash
mv backend/.env .env
ls -la .env backend/.env 2>&1 | head
```

Expected: `.env` exists at root, `backend/.env` does not.

- [ ] **Step 3: No commit needed** (file is gitignored). Skip to Task 4.

### Task 4: Delete the now-stale compose files & nginx dir inside `backend/`

These are about to be replaced at the root; deleting them now keeps the diff readable.

**Files:**
- Delete: `backend/docker-compose.dev.yml`
- Delete: `backend/docker-compose.prod.yml`
- Delete: `backend/nginx/` (entire dir; will be rewritten as `gateway/nginx.*.conf.template`)
- Delete: `backend/.github/workflows/main.yaml` (will be replaced by root workflow)

- [ ] **Step 1: Remove**

Run:
```bash
cd /Users/alexey/projects/ord-people-fs
git rm backend/docker-compose.dev.yml backend/docker-compose.prod.yml
git rm -r backend/nginx
git rm backend/.github/workflows/main.yaml
# remove the now-empty workflows / .github dirs
rmdir backend/.github/workflows backend/.github 2>/dev/null || true
ls backend/ | grep -E '(compose|nginx|.github)' || echo "clean"
```

Expected: `clean`.

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "refactor: remove backend-owned compose, nginx, and workflow (moving to repo root)"
```

### Task 5: Delete the frontend's S3 deploy workflow

**Files:**
- Delete: `frontend/.github/workflows/deploy.yml`

- [ ] **Step 1: Remove**

Run:
```bash
cd /Users/alexey/projects/ord-people-fs
git rm frontend/.github/workflows/deploy.yml
rmdir frontend/.github/workflows frontend/.github 2>/dev/null || true
```

- [ ] **Step 2: Commit**

```bash
git commit -m "refactor: remove frontend S3 deploy workflow (replaced by gateway-served static)"
```

---

## Phase 2 — Build the new services & wiring

### Task 6: Create `gateway/` with Dockerfile, dev config, prod config, entrypoint

The gateway is a standalone nginx image. It must:

1. Contain **only** its own configs + entrypoint — no backend or frontend source.
2. Serve the SPA static files at `${SPA_DOMAIN}` from `/usr/share/nginx/html` (which will be a shared volume populated by the frontend container).
3. Reverse-proxy `${API_DOMAIN}/api/...` and `${API_DOMAIN}/ht` to `backend:8000`.
4. In prod, terminate SSL using certs at `/etc/letsencrypt/...` (bind-mounted at run time).
5. Preserve every security rule from the current `backend/nginx/nginx.prod.conf` (rate limits, bad-bot map, denied extensions, security headers).

**Files:**
- Create: `gateway/Dockerfile`
- Create: `gateway/docker-entrypoint.sh`
- Create: `gateway/nginx.dev.conf.template`
- Create: `gateway/nginx.prod.conf.template`
- Create: `gateway/.dockerignore`

- [ ] **Step 1: Create `gateway/.dockerignore`**

```dockerignore
# Deny-list everything by default; we only want the four files we explicitly COPY.
# These patterns belt-and-braces the COPY commands in the Dockerfile.
*
!Dockerfile
!docker-entrypoint.sh
!nginx.dev.conf.template
!nginx.prod.conf.template
```

- [ ] **Step 2: Create `gateway/Dockerfile`**

```dockerfile
FROM nginx:1.31.1-alpine3.23-slim

# envsubst lives in gettext on alpine
RUN apk add --no-cache gettext

# Both templates live in /etc/nginx/templates/; entrypoint picks one based on NGINX_ENV.
COPY nginx.dev.conf.template  /etc/nginx/templates/nginx.dev.conf.template
COPY nginx.prod.conf.template /etc/nginx/templates/nginx.prod.conf.template
COPY docker-entrypoint.sh /docker-entrypoint.d/40-render-conf.sh

# The shared SPA volume mounts here. Pre-create with safe perms.
RUN mkdir -p /usr/share/nginx/html && chown -R nginx:nginx /usr/share/nginx/html

RUN chmod +x /docker-entrypoint.d/40-render-conf.sh

# nginx:alpine already EXPOSEs 80; we add 443 for prod.
EXPOSE 80 443
```

> The base image's `/docker-entrypoint.sh` runs every executable in `/docker-entrypoint.d/` in order before launching nginx, so we don't override the entrypoint — we just drop our render step in.

- [ ] **Step 3: Create `gateway/docker-entrypoint.sh`**

```sh
#!/bin/sh
set -e

: "${NGINX_ENV:=dev}"
: "${SPA_DOMAIN:=localhost}"
: "${API_DOMAIN:=localhost}"

src="/etc/nginx/templates/nginx.${NGINX_ENV}.conf.template"
dst="/etc/nginx/conf.d/default.conf"

if [ ! -f "$src" ]; then
  echo "gateway: unknown NGINX_ENV='${NGINX_ENV}' (no template at ${src})" >&2
  exit 1
fi

# Only the two domain placeholders are substituted; everything else (nginx vars like $host) is left alone.
envsubst '${SPA_DOMAIN} ${API_DOMAIN}' < "$src" > "$dst"
echo "gateway: rendered ${src} -> ${dst} (SPA_DOMAIN=${SPA_DOMAIN}, API_DOMAIN=${API_DOMAIN})"
```

- [ ] **Step 4: Create `gateway/nginx.dev.conf.template`** (single-port HTTP; SPA at /, API at /api → backend:8000, /ht passthrough for healthchecks)

```nginx
upstream backend_upstream {
    server backend:8000;
    keepalive 16;
}

proxy_http_version 1.1;
proxy_set_header   Connection         "";
proxy_set_header   Host               $host;
proxy_set_header   X-Real-IP          $remote_addr;
proxy_set_header   X-Forwarded-For    $proxy_add_x_forwarded_for;
proxy_set_header   X-Forwarded-Proto  $scheme;
proxy_set_header   X-Forwarded-Host   $host;
proxy_connect_timeout 5s;
proxy_read_timeout    30s;
proxy_send_timeout    10s;

server {
    listen 80;
    server_name ${SPA_DOMAIN} ${API_DOMAIN} localhost;

    client_max_body_size 10M;

    access_log /var/log/nginx/access.log;
    error_log  /var/log/nginx/error.log info;

    # API
    location /api/ {
        proxy_pass http://backend_upstream;
    }

    # Backend healthcheck passthrough (used by dev tooling)
    location = /ht {
        proxy_pass http://backend_upstream;
    }

    # Static media served by the backend (S3 in real life, but the backend has a /media route for dev)
    location /media/ {
        proxy_pass http://backend_upstream;
    }

    # Backend admin
    location /admin {
        proxy_pass http://backend_upstream;
    }

    # SPA
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Hashed Vite assets get a long cache; index.html stays no-cache via the default.
    location ~* \.(js|css|woff2?|svg|png|jpg|jpeg|gif|webp|ico)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        try_files $uri =404;
    }
}
```

- [ ] **Step 5: Create `gateway/nginx.prod.conf.template`**

Faithfully port the existing security rules from `backend/nginx/nginx.prod.conf` (rate-limit zones, conn-limit zones, write_key map, bad_bot map, SSL ciphers, security headers, denied extensions, robots.txt), then add a server block for `${SPA_DOMAIN}` that serves the static SPA.

```nginx
limit_req_zone  $binary_remote_addr zone=api_limit:10m  rate=30r/s;
limit_req_zone  $binary_remote_addr zone=auth_limit:10m rate=2r/s;
limit_req_zone  $write_key          zone=write_limit:10m rate=5r/s;

limit_conn_zone $binary_remote_addr zone=api_conn:10m;
limit_conn_zone $binary_remote_addr zone=auth_conn:10m;
limit_conn_zone $server_name        zone=srv_conn:10m;

map $request_method $write_key {
    default                  "";
    POST                     $binary_remote_addr;
    PUT                      $binary_remote_addr;
    PATCH                    $binary_remote_addr;
    DELETE                   $binary_remote_addr;
}

map $http_user_agent $bad_bot {
    default                                                                     0;
    "~*(AhrefsBot|SemrushBot|DotBot|MJ12bot|MauiBot|ZoominfoBot|PetalBot)"      1;
    "~*(nikto|sqlmap|fimap|nessus|whatweb|Openvas|jbrofuzz|libwhisker|wpscan)"  1;
    "~*(masscan|zgrab|nmap|dirbuster|gobuster|feroxbuster|ffuf)"                1;
    ""                                                                          1;
}

upstream backend_upstream {
    server backend:8000;
    keepalive 32;
}

proxy_http_version 1.1;
proxy_set_header   Connection         "";
proxy_set_header   Host               $host;
proxy_set_header   X-Real-IP          $remote_addr;
proxy_set_header   X-Forwarded-For    $proxy_add_x_forwarded_for;
proxy_set_header   X-Forwarded-Proto  $scheme;
proxy_set_header   X-Forwarded-Host   $host;
proxy_connect_timeout 5s;
proxy_read_timeout    30s;
proxy_send_timeout    10s;

ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384:DHE-RSA-CHACHA20-POLY1305;
ssl_ecdh_curve X25519:prime256v1;
ssl_prefer_server_ciphers off;
ssl_session_timeout 1d;
ssl_session_cache shared:SSL:10m;
ssl_session_tickets off;

server_tokens off;

# --- catch-all: refuse unknown SNI / Host with a TCP-RST-like 444 ---
server {
    listen 80  default_server;
    listen 443 ssl default_server;
    http2 on;
    server_name _;

    ssl_certificate     /etc/letsencrypt/live/${API_DOMAIN}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${API_DOMAIN}/privkey.pem;

    return 444;
}

# --- HTTP -> HTTPS redirects, plus ACME passthrough, for both domains ---
server {
    listen 80;
    server_name ${SPA_DOMAIN} ${API_DOMAIN};

    location ^~ /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

# --- shared security-header snippet repeated in each https server block ---
# (nginx has no `include` directive in this template render path; copy-paste is intentional)

# --- API: app.ord-people.ru ---
server {
    listen 443 ssl;
    http2 on;
    server_name ${API_DOMAIN};

    ssl_certificate     /etc/letsencrypt/live/${API_DOMAIN}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${API_DOMAIN}/privkey.pem;

    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header Referrer-Policy "strict-origin" always;
    add_header Permissions-Policy "geolocation=(), microphone=(), camera=(), payment=()" always;
    add_header Cross-Origin-Opener-Policy "same-origin" always;

    access_log /var/log/nginx/access.log;
    error_log  /var/log/nginx/error.log warn;

    keepalive_timeout 75;
    client_max_body_size 10M;
    client_body_timeout 10s;
    client_header_timeout 10s;
    send_timeout 15s;
    limit_conn srv_conn 2000;
    limit_req_status  429;
    limit_conn_status 429;

    if ($request_method !~ ^(GET|HEAD|POST|PUT|PATCH|DELETE|OPTIONS)$) { return 405; }
    if ($bad_bot) { return 403; }

    location ~* \.(php|aspx|jsp|cgi|env|git|yaml|yml|DS_Store|sql|bak|sh|bash|ini|log|conf|config|xml|toml|lock)$ { return 444; }
    location ~* ^/(dockerfile|dockerignore|makefile|readme|changelog|license)(\..*)?$ { return 444; }
    location ~* /\.(env|git|aws|ssh) { return 444; }
    location ~* /\.env[\.\-] { return 444; }
    location ~* /(wordpress|wp-admin|wp-login|wp-content|wp-includes|wp-) { return 444; }

    location = /robots.txt {
        add_header Content-Type text/plain;
        return 200 "User-agent: *\nDisallow: /\n";
    }

    location ^~ /.well-known/ { return 404; }

    location = /ht {
        allow 127.0.0.1;
        allow 10.0.0.0/8;
        allow 172.16.0.0/12;
        allow 192.168.0.0/16;
        deny  all;
        access_log off;
        proxy_pass http://backend_upstream;
    }

    location / { return 404; }

    location ~ ^/api/auth/ {
        limit_req  zone=auth_limit burst=5 nodelay;
        limit_req  zone=api_limit  burst=60 nodelay;
        limit_conn auth_conn 10;
        limit_conn api_conn  50;
        proxy_pass http://backend_upstream;
    }

    location /api/ {
        limit_req  zone=api_limit burst=60 nodelay;
        limit_req  zone=write_limit burst=15 nodelay;
        limit_conn api_conn 50;
        proxy_pass http://backend_upstream;
    }
}

# --- SPA: ord-people.ru ---
server {
    listen 443 ssl;
    http2 on;
    server_name ${SPA_DOMAIN};

    ssl_certificate     /etc/letsencrypt/live/${SPA_DOMAIN}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${SPA_DOMAIN}/privkey.pem;

    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header Referrer-Policy "strict-origin" always;
    add_header Permissions-Policy "geolocation=(), microphone=(), camera=(), payment=()" always;
    add_header Cross-Origin-Opener-Policy "same-origin" always;

    access_log /var/log/nginx/access.log;
    error_log  /var/log/nginx/error.log warn;

    keepalive_timeout 75;
    client_max_body_size 1M;
    limit_conn srv_conn 2000;

    if ($bad_bot) { return 403; }

    location ~* /\.(env|git|aws|ssh) { return 444; }

    root /usr/share/nginx/html;
    index index.html;

    # SPA: no-cache on the entry HTML, long-cache on hashed assets.
    location = /index.html {
        add_header Cache-Control "no-cache" always;
        try_files /index.html =404;
    }

    location ~* \.(js|css|woff2?|svg|png|jpg|jpeg|gif|webp|ico)$ {
        expires 1y;
        add_header Cache-Control "public, immutable" always;
        try_files $uri =404;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

> Note on the SPA needing its own cert: the user already operates Let's Encrypt on the VPS. The deploy will need a fresh cert for `ord-people.ru` issued before the first prod boot. The plan flags this in Task 11.

- [ ] **Step 5: Make the entrypoint executable & commit**

Run:
```bash
chmod +x gateway/docker-entrypoint.sh
git add gateway/
git commit -m "feat(gateway): standalone nginx image with dev/prod templates"
```

### Task 7: Create the frontend Dockerfile (build → copy to shared volume → exit)

The frontend image's *only* job: produce static assets in a shared volume the gateway reads.

**Files:**
- Create: `frontend/Dockerfile`
- Create: `frontend/.dockerignore`

- [ ] **Step 1: Create `frontend/.dockerignore`**

```dockerignore
node_modules
dist
dist-ssr
.vite
*.local
.env
.env.*
!.env.example
.git
.gitignore
.idea
.playwright-mcp
*.tsbuildinfo
*.log
.DS_Store
README.md
.claude/
# CI configs that are never used in the image
.github/
Dockerfile
.dockerignore
```

- [ ] **Step 2: Create `frontend/Dockerfile`**

```dockerfile
# syntax=docker/dockerfile:1.7

# --- Stage 1: build ---
FROM node:22-alpine AS builder

WORKDIR /build

# Cache npm install: copy lockfiles first.
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm ci --no-audit --no-fund

# Build inputs.
COPY . .

# Vite picks up VITE_* from the build env. Declare them as ARG so docker compose can pass them through.
ARG VITE_API_BASE_URL
ARG VITE_MEDIA_BASE_URL
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL} \
    VITE_MEDIA_BASE_URL=${VITE_MEDIA_BASE_URL}

RUN npm run build


# --- Stage 2: publisher (sole job: copy /dist into the shared volume, then exit) ---
FROM alpine:3.20

# `cp -a` preserves perms; nothing else needed.
WORKDIR /dist
COPY --from=builder /build/dist/ /dist/

# Entrypoint is inlined so this image has zero extra files.
# /spa is the volume mount target; we sync into it on every container start.
ENTRYPOINT ["/bin/sh", "-c", "set -e; rm -rf /spa/*; cp -a /dist/. /spa/; ls /spa | head; echo 'frontend: published to /spa'"]
```

- [ ] **Step 3: Commit**

```bash
git add frontend/Dockerfile frontend/.dockerignore
git commit -m "feat(frontend): multi-stage Dockerfile that publishes static build to a shared volume"
```

### Task 8: Write the unified `.env.example` at the repo root

Single source of truth. Every `ORD__*` name from the backend `.env` is preserved exactly. New vars (frontend `VITE_*`, gateway domains, infra-only knobs read by compose) are added with comments.

**Files:**
- Create: `.env.example`

- [ ] **Step 1: Write the file**

```bash
# ============================================================================
# Monorepo environment — single source of truth for backend + frontend + gateway.
# Copy to .env (gitignored) and fill in real values.
# Naming: backend uses ORD__<section>__<key>; do NOT rename existing keys.
# ============================================================================

# ----- backend: app -----
ORD__APP__DEBUG=false
ORD__APP__SECRET_KEY=replace-me
ORD__APP__DOMAIN=app.ord-people.ru
ORD__APP__ADMIN_PATH=admin
ORD__APP__BEHIND_PROXY=true
ORD__APP__COOKIE_SECURE=true
ORD__APP__ROOT_PATH=
ORD__APP__FORWARDED_ALLOW_IPS=*
ORD__APP__CONTAINER_NAME=ord_people_backend
ORD__APP__ORIGIN_DOMAIN=ord-people.ru

# ----- backend: admin bootstrap -----
ORD__ADMIN__USERNAME=admin
ORD__ADMIN__PASSWORD=replace-me
ORD__ADMIN__FIRST_NAME=Admin
ORD__ADMIN__LAST_NAME=Admin

# ----- backend: auth -----
ORD__AUTH__PEPPER=replace-me
ORD__AUTH__ARGON2_TIME_COST=3
ORD__AUTH__ARGON2_MEMORY_COST=16384
ORD__AUTH__SESSION_TTL=86400

# ----- backend: postgres -----
ORD__POSTGRES__HOST=postgres
ORD__POSTGRES__DB=ord
ORD__POSTGRES__USER=postgres
ORD__POSTGRES__PASSWORD=replace-me
ORD__POSTGRES__PORT=5432
ORD__POSTGRES__POOL_SIZE=10
ORD__POSTGRES__MAX_OVERFLOW=20

# ----- backend: logging -----
ORD__LOG__LEVEL=INFO
ORD__LOG__DB_LEVEL=WARNING
ORD__LOG__JSON_LOGS=false
ORD__LOG__ACCESS_LOG=true
ORD__LOG__TO_FILE=false
ORD__LOG__FILE_PATH=/var/log/backend
ORD__LOG__FILE_MAX_SIZE_MB=10
ORD__LOG__FILE_BACKUP_COUNT=5
ORD__LOG__SLOW_REQUEST_MS=1000

# ----- backend: redis -----
ORD__REDIS__HOST=redis
ORD__REDIS__PASSWORD=replace-me
ORD__REDIS__PORT=6379
ORD__REDIS__DEFAULT_DB=0

# ----- backend: S3 (media; SPA is NOT on S3 anymore, this is purely backend storage) -----
ORD__S3__ACCESS_KEY=replace-me
ORD__S3__SECRET_KEY=replace-me
ORD__S3__ENDPOINT_URL=https://s3.example.com
ORD__S3__BUCKET_NAME=ord-media
ORD__S3__PUBLIC_URL=https://media.example.com

# ----- frontend (baked into the build via VITE_*) -----
# Public API base used by the browser. In prod this is the API domain; in dev "/api/v1" lets the Vite proxy or gateway forward.
VITE_API_BASE_URL=https://app.ord-people.ru/api/v1
VITE_MEDIA_BASE_URL=https://media.example.com

# ----- gateway -----
# Domains the gateway responds on. In dev both are "localhost".
SPA_DOMAIN=ord-people.ru
API_DOMAIN=app.ord-people.ru

# ----- infra: tuning (prod only; dev compose ignores these) -----
BACKEND_IMAGE=ord-people-backend:latest
GATEWAY_IMAGE=ord-people-gateway:latest
FRONTEND_IMAGE=ord-people-frontend:latest

GUNICORN_WORKERS=3
BACKEND_MEMORY_LIMIT=512m
BACKEND_MEMORY_RESERVE=256m
POSTGRES_MEMORY_LIMIT=512m
POSTGRES_MAX_CONNECTIONS=20
POSTGRES_SHARED_BUFFERS=128MB
POSTGRES_WORK_MEM=4MB
POSTGRES_MAINTENANCE_WORK_MEM=32MB
POSTGRES_EFFECTIVE_CACHE_SIZE=384MB
REDIS_MEMORY_LIMIT=256m
REDIS_MAXMEMORY=128mb
NGINX_MEMORY_LIMIT=128m
```

- [ ] **Step 2: Commit**

```bash
git add .env.example
git commit -m "feat: unified .env.example at repo root"
```

### Task 9: Write `docker-compose.dev.yml`

**Files:**
- Create: `docker-compose.dev.yml`

- [ ] **Step 1: Write the file** (port-for-port equivalent of the old backend/docker-compose.dev.yml plus gateway + frontend)

```yaml
x-logging: &default-logging
  driver: json-file
  options:
    max-size: "20m"
    max-file: "5"

services:
  postgres:
    image: postgres:17.10-alpine3.23
    container_name: ord_people_postgres
    ports:
      - "5433:5432"
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: ord
    volumes:
      - pg_data:/var/lib/postgresql/data
    stop_grace_period: 30s
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $$POSTGRES_USER -d $$POSTGRES_DB"]
      interval: 5s
      timeout: 3s
      retries: 3
      start_period: 5s
    logging: *default-logging
    restart: unless-stopped

  redis:
    image: redis:8.6.3-alpine3.23
    container_name: ord_people_redis
    ports:
      - "6380:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD-SHELL", "redis-cli -p 6379 ping | grep PONG"]
      interval: 5s
      timeout: 3s
      retries: 3
    logging: *default-logging
    restart: unless-stopped

  backend:
    build:
      context: ./backend
    container_name: ord_people_backend
    ports:
      - "8001:8000"
    env_file:
      - .env
    environment:
      ORD__APP__DEBUG: "true"
      ORD__APP__COOKIE_SECURE: "false"
      ORD__APP__DOMAIN: "localhost"
      ORD__APP__SECRET_KEY: "dev-secret-key-change-me"
      ORD__APP__FORWARDED_ALLOW_IPS: "*"
      ORD__APP__CONTAINER_NAME: "ord_people_backend"
      ORD__ADMIN__USERNAME: "admin"
      ORD__ADMIN__PASSWORD: "admin"
      ORD__ADMIN__FIRST_NAME: "Admin"
      ORD__ADMIN__LAST_NAME: "Root"
      ORD__AUTH__PEPPER: "dev-pepper"
      ORD__POSTGRES__HOST: "postgres"
      ORD__POSTGRES__DB: "ord"
      ORD__POSTGRES__USER: "postgres"
      ORD__POSTGRES__PASSWORD: "postgres"
      ORD__REDIS__HOST: "redis"
      ORD__LOG__LEVEL: "DEBUG"
      FORWARDED_ALLOW_IPS: "*"
      GUNICORN_WORKERS: "2"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/ht').status==200 else 1)"]
      interval: 10s
      timeout: 3s
      retries: 5
      start_period: 15s
    logging: *default-logging
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      args:
        VITE_API_BASE_URL: "/api/v1"
        VITE_MEDIA_BASE_URL: "http://localhost:8000/media"
    container_name: ord_people_frontend
    volumes:
      - spa_dist:/spa
    restart: "no"   # build-and-exit semantics
    logging: *default-logging

  gateway:
    build:
      context: ./gateway
    container_name: ord_people_gateway
    ports:
      - "8000:80"
    environment:
      NGINX_ENV: dev
      SPA_DOMAIN: localhost
      API_DOMAIN: localhost
    volumes:
      - spa_dist:/usr/share/nginx/html:ro
    depends_on:
      backend:
        condition: service_healthy
      frontend:
        condition: service_completed_successfully
    logging: *default-logging
    restart: unless-stopped

volumes:
  pg_data:
  redis_data:
  spa_dist:
```

> Port mapping rationale: `8000:80` keeps the previous dev URL `http://localhost:8000` working unchanged. Backend stays on `8001:8000` so devs can still hit it directly bypassing the gateway.

- [ ] **Step 2: Commit**

```bash
git add docker-compose.dev.yml
git commit -m "feat: root docker-compose.dev.yml with backend, frontend (build & exit), gateway"
```

### Task 10: Write `docker-compose.prod.yml`

**Files:**
- Create: `docker-compose.prod.yml`

- [ ] **Step 1: Write the file** (mirrors the old prod compose; adds gateway as a separate image; adds frontend as a build-and-exit container; preserves all networks and security defaults)

```yaml
x-logging: &default-logging
  driver: json-file
  options:
    max-size: "100m"
    max-file: "10"

services:
  postgres:
    image: postgres:17.10-alpine3.23
    container_name: ord_people_postgres
    env_file:
      - .env
    environment:
      POSTGRES_USER: ${ORD__POSTGRES__USER}
      POSTGRES_PASSWORD: ${ORD__POSTGRES__PASSWORD}
      POSTGRES_DB: ${ORD__POSTGRES__DB}
    networks:
      - postgres_network
    volumes:
      - pg_data:/var/lib/postgresql/data
    mem_limit: ${POSTGRES_MEMORY_LIMIT}
    command: >
      postgres
      -c max_connections=${POSTGRES_MAX_CONNECTIONS:-20}
      -c shared_buffers=${POSTGRES_SHARED_BUFFERS:-128MB}
      -c work_mem=${POSTGRES_WORK_MEM:-4MB}
      -c maintenance_work_mem=${POSTGRES_MAINTENANCE_WORK_MEM:-32MB}
      -c effective_cache_size=${POSTGRES_EFFECTIVE_CACHE_SIZE:-384MB}
      -c wal_buffers=4MB
      -c checkpoint_completion_target=0.9
      -c random_page_cost=1.1
    stop_grace_period: 30s
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $$POSTGRES_USER -d $$POSTGRES_DB"]
      interval: 5s
      timeout: 3s
      retries: 3
      start_period: 5s
    logging: *default-logging
    restart: unless-stopped

  redis:
    image: redis:8.6.3-alpine3.23
    container_name: ord_people_redis
    env_file:
      - .env
    environment:
      REDIS_PASSWORD: ${ORD__REDIS__PASSWORD}
      REDIS_PORT: ${ORD__REDIS__PORT:-6379}
    command: >
      redis-server
      --requirepass ${ORD__REDIS__PASSWORD}
      --port ${ORD__REDIS__PORT:-6379}
      --maxmemory ${REDIS_MAXMEMORY:-128mb}
      --maxmemory-policy volatile-ttl
    networks:
      - redis_network
    volumes:
      - redis_data:/data
    mem_limit: ${REDIS_MEMORY_LIMIT}
    healthcheck:
      test: ["CMD-SHELL", "redis-cli -p $$REDIS_PORT -a $$REDIS_PASSWORD ping | grep PONG"]
      interval: 5s
      timeout: 3s
      retries: 3
    logging: *default-logging
    restart: unless-stopped

  backend:
    image: ${BACKEND_IMAGE}
    container_name: ord_people_backend
    env_file:
      - .env
    environment:
      ORD__APP__DEBUG: "false"
      ORD__APP__COOKIE_SECURE: "true"
      ORD__APP__BEHIND_PROXY: "true"
      ORD__APP__FORWARDED_ALLOW_IPS: "*"
      ORD__APP__CONTAINER_NAME: "ord_people_backend"
      ORD__POSTGRES__HOST: "postgres"
      ORD__REDIS__HOST: "redis"
      FORWARDED_ALLOW_IPS: "*"
      GUNICORN_WORKERS: ${GUNICORN_WORKERS:-3}
    networks:
      - backend_network
      - redis_network
      - postgres_network
    volumes:
      - /var/log/ord-people:/var/log/ord-people
    mem_limit: ${BACKEND_MEMORY_LIMIT}
    mem_reservation: ${BACKEND_MEMORY_RESERVE}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/ht').status==200 else 1)"]
      interval: 10s
      timeout: 3s
      retries: 5
      start_period: 20s
    logging: *default-logging
    restart: unless-stopped

  frontend:
    image: ${FRONTEND_IMAGE}
    container_name: ord_people_frontend
    volumes:
      - spa_dist:/spa
    restart: "no"
    logging: *default-logging

  gateway:
    image: ${GATEWAY_IMAGE}
    container_name: ord_people_gateway
    ports:
      - "80:80"
      - "443:443"
    env_file:
      - .env
    environment:
      NGINX_ENV: prod
      SPA_DOMAIN: ${SPA_DOMAIN}
      API_DOMAIN: ${API_DOMAIN}
    networks:
      - backend_network
    volumes:
      - spa_dist:/usr/share/nginx/html:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
      - /var/www/certbot:/var/www/certbot:ro
      - /var/log/nginx:/var/log/nginx
    mem_limit: ${NGINX_MEMORY_LIMIT}
    depends_on:
      backend:
        condition: service_healthy
      frontend:
        condition: service_completed_successfully
    logging: *default-logging
    restart: unless-stopped

networks:
  backend_network:
    driver: bridge
  postgres_network:
    driver: bridge
    internal: true
  redis_network:
    driver: bridge
    internal: true

volumes:
  pg_data:
  redis_data:
  spa_dist:
```

- [ ] **Step 2: Commit**

```bash
git add docker-compose.prod.yml
git commit -m "feat: root docker-compose.prod.yml with gateway + frontend init container"
```

---

## Phase 3 — CI/CD pipeline

### Task 11: Write the single GitHub Actions workflow

Replaces both prior workflows. Builds three images in parallel, pushes them, then deploys via SSH. Adds Telegram notifications, preserved from the backend workflow.

**Files:**
- Create: `.github/workflows/deploy.yml`

- [ ] **Step 1: Write the workflow**

Key design decisions:
- **Backend tests** run only when `backend/**` changed. Frontend has no tests right now.
- **Image tags**: same scheme the backend already uses — `${{ secrets.DOCKER_USERNAME }}/ord-people-<service>:latest`. (`ord-people-backend`, `ord-people-frontend`, `ord-people-gateway`.) Replace the old `${{ github.event.repository.name }}` with explicit names since one repo now produces three images.
- **`.env` on the server**: the deploy step still composes the file from GHA secrets + vars, as before. New vars added: `FRONTEND_IMAGE`, `GATEWAY_IMAGE`, `SPA_DOMAIN`, `API_DOMAIN`. The prior `VITE_API_BASE_URL` and `VITE_MEDIA_BASE_URL` are passed to the frontend build as docker build-args (NOT written to the runtime `.env` — they're baked at build time).
- **Cert prerequisite**: the deploy assumes `/etc/letsencrypt/live/${SPA_DOMAIN}/` already exists on the host. Task 12 documents the one-time issuance step.

```yaml
name: Build & Deploy

on:
  push:
    branches: [main]
    paths-ignore:
      - '**.md'
      - '.gitignore'
      - 'docs/**'
  workflow_dispatch:

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    services:
      redis:
        image: redis:8.6.3-alpine3.23
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v6
        with:
          python-version: '3.14'
      - uses: astral-sh/setup-uv@v7
        with:
          enable-cache: true
          cache-dependency-glob: "backend/uv.lock"
      - name: Install dependencies
        working-directory: backend
        run: uv sync --frozen
      - name: Ruff
        working-directory: backend
        run: uv run ruff check .
      - name: Pyright
        working-directory: backend
        run: uv run pyright
      - name: Pytest
        working-directory: backend
        run: uv run pytest --cov=src/ord_people --cov-branch --cov-report=term-missing

  build-backend:
    name: Build backend image
    runs-on: ubuntu-latest
    needs: backend-tests
    outputs:
      image: ${{ steps.meta.outputs.image }}
    steps:
      - uses: actions/checkout@v6
      - uses: docker/setup-buildx-action@v4
      - uses: docker/login-action@v4
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
      - id: meta
        run: echo "image=${{ secrets.DOCKER_USERNAME }}/ord-people-backend:latest" >> "$GITHUB_OUTPUT"
      - uses: docker/build-push-action@v7
        with:
          context: ./backend
          push: true
          tags: ${{ steps.meta.outputs.image }}
          cache-from: type=gha,scope=backend
          cache-to: type=gha,mode=max,scope=backend

  build-frontend:
    name: Build frontend image
    runs-on: ubuntu-latest
    outputs:
      image: ${{ steps.meta.outputs.image }}
    steps:
      - uses: actions/checkout@v6
      - uses: docker/setup-buildx-action@v4
      - uses: docker/login-action@v4
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
      - id: meta
        run: echo "image=${{ secrets.DOCKER_USERNAME }}/ord-people-frontend:latest" >> "$GITHUB_OUTPUT"
      - uses: docker/build-push-action@v7
        with:
          context: ./frontend
          push: true
          tags: ${{ steps.meta.outputs.image }}
          build-args: |
            VITE_API_BASE_URL=${{ vars.VITE_API_BASE_URL }}
            VITE_MEDIA_BASE_URL=${{ vars.VITE_MEDIA_BASE_URL }}
          cache-from: type=gha,scope=frontend
          cache-to: type=gha,mode=max,scope=frontend

  build-gateway:
    name: Build gateway image
    runs-on: ubuntu-latest
    outputs:
      image: ${{ steps.meta.outputs.image }}
    steps:
      - uses: actions/checkout@v6
      - uses: docker/setup-buildx-action@v4
      - uses: docker/login-action@v4
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
      - id: meta
        run: echo "image=${{ secrets.DOCKER_USERNAME }}/ord-people-gateway:latest" >> "$GITHUB_OUTPUT"
      - uses: docker/build-push-action@v7
        with:
          context: ./gateway
          push: true
          tags: ${{ steps.meta.outputs.image }}
          cache-from: type=gha,scope=gateway
          cache-to: type=gha,mode=max,scope=gateway

  deploy:
    runs-on: ubuntu-latest
    needs: [build-backend, build-frontend, build-gateway]
    steps:
      - uses: actions/checkout@v6
      - name: Copy compose to VPS
        uses: appleboy/scp-action@master
        with:
          host: ${{ secrets.HOST }}
          username: ${{ secrets.USER }}
          key: ${{ secrets.SSH_KEY }}
          passphrase: ${{ secrets.PASSPHRASE }}
          port: ${{ secrets.PORT }}
          source: "docker-compose.prod.yml"
          target: "/opt/ord-people"
      - name: Create .env and restart images
        uses: appleboy/ssh-action@master
        env:
          BACKEND_IMAGE:  ${{ needs.build-backend.outputs.image }}
          FRONTEND_IMAGE: ${{ needs.build-frontend.outputs.image }}
          GATEWAY_IMAGE:  ${{ needs.build-gateway.outputs.image }}

          # --- non-sensitive (repository variables) ---
          SPA_DOMAIN: ${{ vars.SPA_DOMAIN }}
          API_DOMAIN: ${{ vars.API_DOMAIN }}
          ORD__APP__DOMAIN: ${{ vars.ORD__APP__DOMAIN }}
          ORD__APP__ORIGIN_DOMAIN: ${{ vars.ORD__APP__ORIGIN_DOMAIN }}
          ORD__APP__ADMIN_PATH: ${{ vars.ORD__APP__ADMIN_PATH }}
          ORD__ADMIN__USERNAME: ${{ vars.ORD__ADMIN__USERNAME }}
          ORD__ADMIN__FIRST_NAME: ${{ vars.ORD__ADMIN__FIRST_NAME }}
          ORD__ADMIN__LAST_NAME: ${{ vars.ORD__ADMIN__LAST_NAME }}
          ORD__POSTGRES__USER: ${{ vars.ORD__POSTGRES__USER }}
          ORD__POSTGRES__DB: ${{ vars.ORD__POSTGRES__DB }}
          ORD__POSTGRES__PORT: ${{ vars.ORD__POSTGRES__PORT }}
          ORD__REDIS__PORT: ${{ vars.ORD__REDIS__PORT }}
          ORD__S3__ENDPOINT_URL: ${{ vars.ORD__S3__ENDPOINT_URL }}
          ORD__S3__BUCKET_NAME: ${{ vars.ORD__S3__BUCKET_NAME }}
          ORD__S3__PUBLIC_URL: ${{ vars.ORD__S3__PUBLIC_URL }}
          ORD__LOG__LEVEL: ${{ vars.ORD__LOG__LEVEL }}
          ORD__LOG__JSON_LOGS: ${{ vars.ORD__LOG__JSON_LOGS }}
          ORD__LOG__TO_FILE: ${{ vars.ORD__LOG__TO_FILE }}
          GUNICORN_WORKERS: ${{ vars.GUNICORN_WORKERS }}
          BACKEND_MEMORY_LIMIT: ${{ vars.BACKEND_MEMORY_LIMIT }}
          BACKEND_MEMORY_RESERVE: ${{ vars.BACKEND_MEMORY_RESERVE }}
          POSTGRES_MEMORY_LIMIT: ${{ vars.POSTGRES_MEMORY_LIMIT }}
          POSTGRES_MAX_CONNECTIONS: ${{ vars.POSTGRES_MAX_CONNECTIONS }}
          POSTGRES_SHARED_BUFFERS: ${{ vars.POSTGRES_SHARED_BUFFERS }}
          POSTGRES_WORK_MEM: ${{ vars.POSTGRES_WORK_MEM }}
          POSTGRES_MAINTENANCE_WORK_MEM: ${{ vars.POSTGRES_MAINTENANCE_WORK_MEM }}
          POSTGRES_EFFECTIVE_CACHE_SIZE: ${{ vars.POSTGRES_EFFECTIVE_CACHE_SIZE }}
          REDIS_MEMORY_LIMIT: ${{ vars.REDIS_MEMORY_LIMIT }}
          REDIS_MAXMEMORY: ${{ vars.REDIS_MAXMEMORY }}
          NGINX_MEMORY_LIMIT: ${{ vars.NGINX_MEMORY_LIMIT }}

          # --- secrets ---
          ORD__APP__SECRET_KEY: ${{ secrets.ORD__APP__SECRET_KEY }}
          ORD__ADMIN__PASSWORD: ${{ secrets.ORD__ADMIN__PASSWORD }}
          ORD__AUTH__PEPPER: ${{ secrets.ORD__AUTH__PEPPER }}
          ORD__POSTGRES__PASSWORD: ${{ secrets.ORD__POSTGRES__PASSWORD }}
          ORD__REDIS__PASSWORD: ${{ secrets.ORD__REDIS__PASSWORD }}
          ORD__S3__ACCESS_KEY: ${{ secrets.ORD__S3__ACCESS_KEY }}
          ORD__S3__SECRET_KEY: ${{ secrets.ORD__S3__SECRET_KEY }}
        with:
          host: ${{ secrets.HOST }}
          username: ${{ secrets.USER }}
          key: ${{ secrets.SSH_KEY }}
          passphrase: ${{ secrets.PASSPHRASE }}
          port: ${{ secrets.PORT }}
          envs: >
            BACKEND_IMAGE,FRONTEND_IMAGE,GATEWAY_IMAGE,
            SPA_DOMAIN,API_DOMAIN,
            ORD__APP__DOMAIN,ORD__APP__ORIGIN_DOMAIN,ORD__APP__ADMIN_PATH,ORD__APP__SECRET_KEY,
            ORD__ADMIN__USERNAME,ORD__ADMIN__FIRST_NAME,ORD__ADMIN__LAST_NAME,ORD__ADMIN__PASSWORD,
            ORD__AUTH__PEPPER,
            ORD__POSTGRES__USER,ORD__POSTGRES__DB,ORD__POSTGRES__PORT,ORD__POSTGRES__PASSWORD,
            ORD__REDIS__PORT,ORD__REDIS__PASSWORD,
            ORD__S3__ACCESS_KEY,ORD__S3__SECRET_KEY,ORD__S3__ENDPOINT_URL,ORD__S3__BUCKET_NAME,ORD__S3__PUBLIC_URL,
            ORD__LOG__LEVEL,ORD__LOG__JSON_LOGS,ORD__LOG__TO_FILE,
            GUNICORN_WORKERS,
            BACKEND_MEMORY_LIMIT,BACKEND_MEMORY_RESERVE,
            POSTGRES_MEMORY_LIMIT,POSTGRES_MAX_CONNECTIONS,POSTGRES_SHARED_BUFFERS,POSTGRES_WORK_MEM,POSTGRES_MAINTENANCE_WORK_MEM,POSTGRES_EFFECTIVE_CACHE_SIZE,
            REDIS_MEMORY_LIMIT,REDIS_MAXMEMORY,
            NGINX_MEMORY_LIMIT
          script: |
            set -e
            cd /opt/ord-people
            mkdir -p /var/log/ord-people /var/log/nginx
            umask 077
            {
              printf 'BACKEND_IMAGE=%s\n'                       "$BACKEND_IMAGE"
              printf 'FRONTEND_IMAGE=%s\n'                      "$FRONTEND_IMAGE"
              printf 'GATEWAY_IMAGE=%s\n'                       "$GATEWAY_IMAGE"
              printf 'SPA_DOMAIN=%s\n'                          "$SPA_DOMAIN"
              printf 'API_DOMAIN=%s\n'                          "$API_DOMAIN"
              printf 'ORD__APP__DOMAIN=%s\n'                    "$ORD__APP__DOMAIN"
              printf 'ORD__APP__ORIGIN_DOMAIN=%s\n'             "$ORD__APP__ORIGIN_DOMAIN"
              printf 'ORD__APP__ADMIN_PATH=%s\n'                "$ORD__APP__ADMIN_PATH"
              printf 'ORD__APP__SECRET_KEY=%s\n'                "$ORD__APP__SECRET_KEY"
              printf 'ORD__ADMIN__USERNAME=%s\n'                "$ORD__ADMIN__USERNAME"
              printf 'ORD__ADMIN__FIRST_NAME=%s\n'              "$ORD__ADMIN__FIRST_NAME"
              printf 'ORD__ADMIN__LAST_NAME=%s\n'               "$ORD__ADMIN__LAST_NAME"
              printf 'ORD__ADMIN__PASSWORD=%s\n'                "$ORD__ADMIN__PASSWORD"
              printf 'ORD__AUTH__PEPPER=%s\n'                   "$ORD__AUTH__PEPPER"
              printf 'ORD__POSTGRES__USER=%s\n'                 "$ORD__POSTGRES__USER"
              printf 'ORD__POSTGRES__DB=%s\n'                   "$ORD__POSTGRES__DB"
              printf 'ORD__POSTGRES__PORT=%s\n'                 "$ORD__POSTGRES__PORT"
              printf 'ORD__POSTGRES__PASSWORD=%s\n'             "$ORD__POSTGRES__PASSWORD"
              printf 'ORD__REDIS__PORT=%s\n'                    "$ORD__REDIS__PORT"
              printf 'ORD__REDIS__PASSWORD=%s\n'                "$ORD__REDIS__PASSWORD"
              printf 'ORD__S3__ACCESS_KEY=%s\n'                 "$ORD__S3__ACCESS_KEY"
              printf 'ORD__S3__SECRET_KEY=%s\n'                 "$ORD__S3__SECRET_KEY"
              printf 'ORD__S3__ENDPOINT_URL=%s\n'               "$ORD__S3__ENDPOINT_URL"
              printf 'ORD__S3__BUCKET_NAME=%s\n'                "$ORD__S3__BUCKET_NAME"
              printf 'ORD__S3__PUBLIC_URL=%s\n'                 "$ORD__S3__PUBLIC_URL"
              printf 'ORD__LOG__LEVEL=%s\n'                     "$ORD__LOG__LEVEL"
              printf 'ORD__LOG__JSON_LOGS=%s\n'                 "$ORD__LOG__JSON_LOGS"
              printf 'ORD__LOG__TO_FILE=%s\n'                   "$ORD__LOG__TO_FILE"
              printf 'GUNICORN_WORKERS=%s\n'                    "$GUNICORN_WORKERS"
              printf 'BACKEND_MEMORY_LIMIT=%s\n'                "$BACKEND_MEMORY_LIMIT"
              printf 'BACKEND_MEMORY_RESERVE=%s\n'              "$BACKEND_MEMORY_RESERVE"
              printf 'POSTGRES_MEMORY_LIMIT=%s\n'               "$POSTGRES_MEMORY_LIMIT"
              printf 'POSTGRES_MAX_CONNECTIONS=%s\n'            "$POSTGRES_MAX_CONNECTIONS"
              printf 'POSTGRES_SHARED_BUFFERS=%s\n'             "$POSTGRES_SHARED_BUFFERS"
              printf 'POSTGRES_WORK_MEM=%s\n'                   "$POSTGRES_WORK_MEM"
              printf 'POSTGRES_MAINTENANCE_WORK_MEM=%s\n'       "$POSTGRES_MAINTENANCE_WORK_MEM"
              printf 'POSTGRES_EFFECTIVE_CACHE_SIZE=%s\n'       "$POSTGRES_EFFECTIVE_CACHE_SIZE"
              printf 'REDIS_MEMORY_LIMIT=%s\n'                  "$REDIS_MEMORY_LIMIT"
              printf 'REDIS_MAXMEMORY=%s\n'                     "$REDIS_MAXMEMORY"
              printf 'NGINX_MEMORY_LIMIT=%s\n'                  "$NGINX_MEMORY_LIMIT"
            } > .env
            chmod 600 .env
            docker compose -f docker-compose.prod.yml pull
            docker compose -f docker-compose.prod.yml up -d --remove-orphans
            docker image prune -af

  notify:
    name: Send Telegram Notification
    runs-on: ubuntu-latest
    needs: deploy
    if: always()
    steps:
      - if: needs.deploy.result == 'success'
        uses: appleboy/telegram-action@master
        with:
          to: ${{ secrets.TELEGRAM_TO }}
          token: ${{ secrets.TELEGRAM_TOKEN }}
          message: |
            🚀 ord-people deployed successfully!
            📝 Commit: ${{ github.event.head_commit.message }}
            👤 Author: ${{ github.event.head_commit.author.name }}
      - if: needs.deploy.result == 'failure'
        uses: appleboy/telegram-action@master
        with:
          to: ${{ secrets.TELEGRAM_TO }}
          token: ${{ secrets.TELEGRAM_TOKEN }}
          message: |
            ❌ Deploy failed for ord-people!
            📝 Commit: ${{ github.event.head_commit.message }}
            🔍 Details: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/deploy.yml
git commit -m "ci: unified build & deploy pipeline for backend, frontend, gateway"
```

### Task 12: Document the one-time VPS migration steps

The deploy job assumes a few things on the VPS that don't exist yet (a cert for `ord-people.ru`, the new repo location, new GH variables/secrets). Capture this as a checklist in the README so the human running the first deploy doesn't get surprised.

**Files:**
- Modify: `README.md` (append a `## Deployment migration checklist` section)

- [ ] **Step 1: Append to README.md**

```markdown
## Deployment migration checklist (one-time)

Before the first push to `main` after this restructure:

1. **GitHub Variables** (Settings → Secrets and variables → Actions → Variables): add the new vars
   - `SPA_DOMAIN` = `ord-people.ru`
   - `API_DOMAIN` = `app.ord-people.ru`
   - `VITE_API_BASE_URL` = `https://app.ord-people.ru/api/v1`
   - `VITE_MEDIA_BASE_URL` = `<the same S3 public URL the backend uses>`
   - Confirm `ORD__APP__DOMAIN` = `app.ord-people.ru` (was `backend.ord-people.ru`)
   - Confirm `ORD__APP__ORIGIN_DOMAIN` = `ord-people.ru`
2. **GitHub Secrets**: no new secrets, but remove the now-unused `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` (S3 deploy is gone).
3. **VPS DNS**: ensure both `ord-people.ru` and `app.ord-people.ru` resolve to the VPS IP.
4. **VPS Let's Encrypt certs**: issue a cert for `ord-people.ru` (the API cert at `app.ord-people.ru` already exists if you previously had `backend.ord-people.ru` — if not, issue both). With certbot already on the host:
   ```
   sudo certbot certonly --webroot -w /var/www/certbot -d ord-people.ru
   sudo certbot certonly --webroot -w /var/www/certbot -d app.ord-people.ru
   ```
5. **VPS path**: the deploy now writes to `/opt/ord-people` (not `/opt/ord-people-frontend` or `/opt/ord-people-backend`). Move or remove the old dirs once the new deploy succeeds.
6. **Old S3 SPA bucket**: after the first successful deploy, the SPA stops being served from S3. Empty/delete the bucket at your leisure.
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: deployment migration checklist for monorepo cutover"
```

---

## Phase 4 — Verification

### Task 13: Verify dev compose builds and serves

This is the integration test for the whole plan. We don't have unit tests for Dockerfiles; the verification is: does `docker compose up` produce a working stack?

- [ ] **Step 1: Ensure a `.env` exists at root**

Run:
```bash
cd /Users/alexey/projects/ord-people-fs
test -f .env && echo "ok: .env present" || cp .env.example .env
```

For dev, the compose file hard-codes the dev-relevant overrides so the `.env` only needs the secrets (admin password, S3 creds, etc.) the backend would otherwise refuse to start without. If you copied `.env.example`, you may need to fill in `ORD__S3__*` and friends.

- [ ] **Step 2: Build and start the stack**

Run:
```bash
docker compose -f docker-compose.dev.yml up --build -d
```

Expected: postgres, redis, backend, frontend, gateway all come up. Frontend exits 0 after publishing to the volume.

- [ ] **Step 3: Wait for backend healthy, then verify**

Run:
```bash
# wait up to 60s for backend healthcheck
for i in $(seq 1 30); do
  status=$(docker inspect -f '{{.State.Health.Status}}' ord_people_backend 2>/dev/null || echo missing)
  echo "[$i] backend health: $status"
  [ "$status" = "healthy" ] && break
  sleep 2
done
```

Expected: ends with `healthy`.

- [ ] **Step 4: Hit the SPA through the gateway**

Run:
```bash
curl -sS -o /dev/null -w "%{http_code}\n" http://localhost:8000/
curl -sS http://localhost:8000/ | head -5
```

Expected: `200`, and the first lines of the Vite-built `index.html`.

- [ ] **Step 5: Hit the API through the gateway**

Run:
```bash
curl -sS -o /dev/null -w "%{http_code}\n" http://localhost:8000/api/v1/
curl -sS -o /dev/null -w "%{http_code}\n" http://localhost:8000/ht
```

Expected: the API responds (status depends on whether `/api/v1/` is a real endpoint — `404` from FastAPI is acceptable, what matters is it's *not* the SPA's `index.html`). `/ht` returns `200`.

- [ ] **Step 6: Confirm image isolation**

Run:
```bash
# Backend image must not have frontend source
docker run --rm --entrypoint sh "$(docker compose -f docker-compose.dev.yml images -q backend)" -c "ls /app | grep -Ei 'vite|react|package.json|node_modules' || echo 'isolated: no frontend files in backend image'"

# Gateway image must not have backend or frontend source
gw_img=$(docker compose -f docker-compose.dev.yml images -q gateway)
docker run --rm --entrypoint sh "$gw_img" -c "ls / | tr ' ' '\n' | grep -E '^(app|build|src)$' || echo 'isolated: no backend/frontend source in gateway image'"
docker run --rm --entrypoint sh "$gw_img" -c "find /etc/nginx -name 'default.conf' -o -name '*.template' | head"

# Frontend image must contain ONLY /dist + minimal alpine
fe_img=$(docker compose -f docker-compose.dev.yml images -q frontend)
docker run --rm --entrypoint sh "$fe_img" -c "ls / && ls /dist | head"
```

Expected:
- backend prints `isolated: no frontend files in backend image`
- gateway prints `isolated: no backend/frontend source in gateway image` and lists the rendered `default.conf`
- frontend lists root dirs (no `app/`, no `build/`, no `node_modules/`) plus `/dist/...`

- [ ] **Step 7: Tear down**

Run:
```bash
docker compose -f docker-compose.dev.yml down -v
```

- [ ] **Step 8: Commit nothing** — this was verification only. Move to Task 14.

### Task 14: Final cleanup & commit

- [ ] **Step 1: Sanity check the tree**

Run:
```bash
cd /Users/alexey/projects/ord-people-fs
ls -1
```

Expected: `.env`, `.env.example`, `.github`, `.gitignore`, `README.md`, `backend`, `docker-compose.dev.yml`, `docker-compose.prod.yml`, `frontend`, `gateway`, plus `docs/` if the plan lives here.

- [ ] **Step 2: Confirm no stale `ord-people*` dirs remain**

Run:
```bash
ls -1 | grep -E '^ord-people' && echo "STALE — investigate" || echo "clean"
```

Expected: `clean`.

- [ ] **Step 3: Show final git log**

Run:
```bash
git log --oneline
```

Expected: ~12 commits, narrating the restructure.

---

## Self-Review

**Spec coverage:**
- ✅ Merge into single monorepo with `gateway/`, `backend/`, `frontend/` (Tasks 1, 2, 6, 7)
- ✅ Extract Nginx into standalone `gateway/` (Task 6) with Dockerfile, SPA serving from shared volume RO, API proxy, SSL via Let's Encrypt bind-mount
- ✅ Frontend Dockerfile multi-stage, sole purpose populates shared volume (Task 7)
- ✅ Strict isolation between services (Tasks 6, 7 `.dockerignore` + verified in Task 13 step 6)
- ✅ Synchronised `.env` source of truth (Tasks 3, 8); no backend keys renamed (Task 8 verified against `.env`)
- ✅ Two compose files (Tasks 9, 10)
- ✅ Single GitHub Actions workflow (Task 11) replacing both old ones (Tasks 4, 5)
- ✅ Old nginx removed from backend (Task 4); S3 deploy removed from frontend (Task 5)
- ✅ `.dockerignore` for each service (Tasks 6, 7; backend's existing one preserved)
- ✅ `docker compose -f docker-compose.dev.yml up --build` tested (Task 13)

**Placeholder scan:** No `TBD`/`TODO`/"add appropriate" entries; every code block is concrete.

**Type/name consistency:**
- Shared volume name `spa_dist` is consistent across the two compose files and the gateway's expected mount `/usr/share/nginx/html`.
- Frontend mount target inside the frontend container is `/spa` in both compose files and matches the Dockerfile's ENTRYPOINT (`cp -a /dist/. /spa/`).
- Env var `NGINX_ENV` is set in both compose files and read by `gateway/docker-entrypoint.sh`.
- Image var names (`BACKEND_IMAGE`, `FRONTEND_IMAGE`, `GATEWAY_IMAGE`) match between the workflow's env block, the heredoc that writes `.env`, and `docker-compose.prod.yml`.
- `SPA_DOMAIN` / `API_DOMAIN` flow consistently: GH vars → workflow env → `.env` on host → compose → gateway env → `envsubst` in templates.

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-05-31-monorepo-restructure.md`. Two execution options:**

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

**Which approach?**
