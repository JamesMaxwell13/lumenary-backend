#!/usr/bin/env bash

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/vps-common.sh"
require_runtime

exec 9>"$PROJECT_ROOT/.vps-update.lock"
flock -n 9 || { echo "Another deployment is already running." >&2; exit 1; }

required=(
  SITE_HOST SITE_URL BACKEND_IMAGE FRONTEND_IMAGE DJANGO_SECRET_KEY
  POSTGRES_DB POSTGRES_USER POSTGRES_PASSWORD AWS_ACCESS_KEY_ID
  AWS_SECRET_ACCESS_KEY AWS_STORAGE_BUCKET_NAME AWS_S3_ENDPOINT_URL
  AWS_S3_PUBLIC_URL
)
missing=()
for key in "${required[@]}"; do
  value="$(env_value "$key")"
  if [[ -z "$value" || "$value" == "change-me" || "$value" == *"/owner/"* ]]; then
    missing+=("$key")
  fi
done
if (( ${#missing[@]} )); then
  printf 'Missing or placeholder configuration: %s\n' "$(IFS=', '; echo "${missing[*]}")" >&2
  exit 1
fi

chmod 600 "$ENV_FILE"
cd "$PROJECT_ROOT"
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git pull --ff-only
fi

compose config --quiet
compose pull postgres minio backend frontend
compose up -d --wait postgres minio
compose run --rm --no-deps backend python manage.py ensure_minio_bucket
"$PROJECT_ROOT/scripts/vps-backup.sh"
compose run --rm --no-deps backend python manage.py migrate --noinput
compose up -d --remove-orphans --wait backend frontend

site_url="$(env_value SITE_URL)"
curl --fail --retry 10 --retry-delay 3 "$site_url/healthz"
curl --fail --retry 10 --retry-delay 3 "$site_url/api/v1/health/"
docker image prune -f
compose ps
