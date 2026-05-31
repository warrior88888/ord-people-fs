# ord-people-fs

Monorepo for the ord-people project.

- `backend/` — FastAPI service (see `backend/README.md`)
- `frontend/` — React/Vite SPA (see `frontend/README.md`)
- `gateway/` — nginx reverse proxy + SPA host

Local development: `docker compose -f docker-compose.dev.yml up --build`.
