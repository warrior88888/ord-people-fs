FROM nginx:1.31.1-alpine3.23-slim

# envsubst lives in gettext on alpine
RUN apk add --no-cache gettext

# Templates live in /etc/gateway/ so the base image's 20-envsubst-on-templates.sh
# does not auto-render them both into conf.d/ and cause duplicate-listen conflicts.
COPY nginx.dev.conf.template  /etc/gateway/nginx.dev.conf.template
COPY nginx.prod.conf.template /etc/gateway/nginx.prod.conf.template
COPY docker-entrypoint.sh /docker-entrypoint.d/40-render-conf.sh

# The shared SPA volume mounts here. Pre-create with safe perms.
RUN mkdir -p /usr/share/nginx/html && chown -R nginx:nginx /usr/share/nginx/html

RUN chmod +x /docker-entrypoint.d/40-render-conf.sh

# nginx:alpine already EXPOSEs 80; we add 443 for prod.
EXPOSE 80 443
