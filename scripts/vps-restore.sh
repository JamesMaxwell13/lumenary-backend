#!/usr/bin/env bash

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/vps-common.sh"
require_runtime

dump_path="${1:-}"
confirmation="${2:-}"
if [[ -z "$dump_path" || ! -f "$dump_path" ]]; then
  echo "Usage: $0 /path/to/lumenary.dump --yes" >&2
  exit 1
fi
if [[ "$confirmation" != "--yes" ]]; then
  echo "Restore replaces the current database. Re-run with --yes." >&2
  exit 1
fi

"$PROJECT_ROOT/scripts/vps-backup.sh"
compose up -d --wait postgres
compose exec -T postgres sh -c 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists --no-owner --no-acl --exit-on-error' < "$dump_path"
compose run --rm --no-deps backend python manage.py migrate --noinput
compose up -d --wait backend frontend
echo "Database restored from: $dump_path"
