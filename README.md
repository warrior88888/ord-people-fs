# ord-people-fs

Monorepo for the ord-people project.

- `backend/` — FastAPI service (see `backend/README.md`)
- `frontend/` — React/Vite SPA (see `frontend/README.md`)
- `gateway/` — nginx reverse proxy + SPA host

Local development: `docker compose -f docker-compose.dev.yml up --build`.

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
