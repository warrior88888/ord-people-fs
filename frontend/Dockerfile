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
