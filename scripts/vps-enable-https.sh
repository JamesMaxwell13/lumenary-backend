#!/usr/bin/env bash

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/vps-common.sh"
require_runtime
command -v certbot >/dev/null || { echo "certbot is not installed on the VPS" >&2; exit 1; }

site_host="$(env_value SITE_HOST)"
email="$(env_value LETSENCRYPT_EMAIL)"
if [[ -z "$email" || "$email" == "admin@example.com" ]]; then
  echo "Configure LETSENCRYPT_EMAIL in .env." >&2
  exit 1
fi
if [[ "$site_host" =~ ^[0-9.]+$ ]]; then
  echo "Let's Encrypt requires a public domain in SITE_HOST, not an IP address." >&2
  exit 1
fi

mkdir -p "$PROJECT_ROOT/certbot/www" "$PROJECT_ROOT/certbot/conf" \
  "$PROJECT_ROOT/certbot/work" "$PROJECT_ROOT/certbot/logs"
set_env_value ENABLE_HTTPS false
compose up -d --wait frontend

certbot certonly --webroot --webroot-path "$PROJECT_ROOT/certbot/www" --config-dir "$PROJECT_ROOT/certbot/conf" --work-dir "$PROJECT_ROOT/certbot/work" --logs-dir "$PROJECT_ROOT/certbot/logs" --domain "$site_host" --email "$email" --agree-tos --no-eff-email

set_env_value ENABLE_HTTPS true
set_env_value SITE_URL "https://$site_host"
set_env_value DJANGO_CSRF_TRUSTED_ORIGINS "https://$site_host"
set_env_value CORS_ALLOWED_ORIGINS "https://$site_host"
set_env_value ADMIN_BASE_URL "https://$site_host"
set_env_value AWS_S3_PUBLIC_URL "https://$site_host/media"
set_env_value SESSION_COOKIE_SECURE true
set_env_value CSRF_COOKIE_SECURE true
set_env_value SECURE_SSL_REDIRECT true
set_env_value SECURE_HSTS_SECONDS 31536000

compose up -d --force-recreate --wait backend frontend
"$PROJECT_ROOT/scripts/vps-status.sh"
echo "HTTPS enabled for https://$site_host"
