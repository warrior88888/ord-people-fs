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
