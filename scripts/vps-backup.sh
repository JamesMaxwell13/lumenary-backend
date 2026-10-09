#!/usr/bin/env bash

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/vps-common.sh"
require_runtime

mkdir -p "$PROJECT_ROOT/backups"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
target="$PROJECT_ROOT/backups/lumenary-$timestamp.dump"
temporary="$target.tmp"

compose exec -T postgres sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc --no-owner --no-acl' > "$temporary"
mv "$temporary" "$target"

retention_days="$(env_value BACKUP_RETENTION_DAYS)"
retention_days="${retention_days:-14}"
find "$PROJECT_ROOT/backups" -type f -name 'lumenary-*.dump' -mtime "+$retention_days" -delete
echo "Database backup created: $target"
