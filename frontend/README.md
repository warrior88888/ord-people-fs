# Простые люди, большие дела (frontend)

SPA на React 19 + Vite + Tailwind v4 + React Query. Бэкенд (FastAPI) предоставляет API
с сессионной авторизацией через cookie.

## Стек

- React 19, TypeScript, Vite
- React Router v7
- TanStack Query v5
- Tailwind CSS v4 (CSS-first, токены через `@theme` в `src/index.css`)
- openapi-typescript (генерация типов)

## Локальный запуск

```bash
npm install
cp .env.example .env.local   # заполните значения
npm run dev
```

В dev режиме фронт ходит на API через Vite-прокси: запросы к `/api` форвардятся
на `VITE_DEV_API_PROXY_TARGET` (по умолчанию `http://localhost:8000`).
Это даёт same-origin и cookie-сессии без правок CORS.

## Переменные окружения

| Переменная | Назначение | Где задаётся |
| --- | --- | --- |
| `VITE_API_BASE_URL` | Базовый URL API, вшивается в сборку | `.env.local` / GitHub `vars` |
| `VITE_MEDIA_BASE_URL` | Базовый URL медиа (S3/CDN), вшивается в сборку | `.env.local` / GitHub `vars` |
| `VITE_DEV_API_PROXY_TARGET` | Цель Vite-прокси для `/api` в dev | `.env.local` |

Файлы `.env*` (кроме `.env.example`) в репозиторий не коммитятся.

## Генерация типов API

```bash
npm run gen:api   # читает ./openapi.json и пишет src/api/schema.ts
```

## Сборка

```bash
npm run build
npm run preview
```

Vite добавляет content-hash к именам файлов - это и есть cache-busting.

## Деплой (GitHub Actions → S3)

Workflow `.github/workflows/deploy.yml` срабатывает на push в `main` и делает
два прохода: ассеты с длинным кэшем, `index.html` с `no-cache`.

Все URL и имя бакета берутся из GitHub Actions переменных и секретов.

**Secrets** (`Settings → Secrets and variables → Actions → Secrets`):

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

**Variables** (`Settings → Secrets and variables → Actions → Variables`):

- `VITE_API_BASE_URL` - публичный URL API (напр. `https://backend.example.com/api/v1`)
- `VITE_MEDIA_BASE_URL` - публичный URL медиа
- `S3_BUCKET` - имя бакета для статики
- `S3_ENDPOINT` - endpoint S3-совместимого хранилища
- `S3_REGION` - регион

## Архитектура

```
src/
  api/           client.ts, types.ts, queries/*
  components/    Layout, PostCard, PostFeed, ReactionBar, CommentList, ...
  pages/         Home, Users, UserProfile, PostDetail, PostEditor, Login, Register, About, NotFound
  hooks/         useIntersection
  lib/           constants, format
  index.css      Tailwind v4 + дизайн-токены
```

- Авторизация - только `credentials: "include"`, без localStorage.
- Списки - `useInfiniteQuery` + IntersectionObserver.
- На 429 клиент уважает `Retry-After` и делает до двух ретраев.
- Пользовательский текст рендерится только как plain text.
