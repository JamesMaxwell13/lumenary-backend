#!/usr/bin/env bash

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/vps-common.sh"
require_runtime
command -v certbot >/dev/null || { echo "certbot is not installed on the VPS" >&2; exit 1; }

certbot renew --config-dir "$PROJECT_ROOT/certbot/conf" --work-dir "$PROJECT_ROOT/certbot/work" --logs-dir "$PROJECT_ROOT/certbot/logs" --webroot-path "$PROJECT_ROOT/certbot/www" --deploy-hook "docker compose --env-file '$ENV_FILE' -f '$COMPOSE_FILE' exec -T frontend nginx -s reload"
