# Production deployment

The primary production target is a hoster.by VPS or Cloud VPS with Docker and
the Compose plugin. The backend repository owns the shared deployment files;
the frontend repository only builds and updates `FRONTEND_IMAGE`.

1. Copy `.env.production.example` to `${VPS_APP_DIR}/.env` and replace every
   placeholder. Set `VITE_API_BASE_URL=/api/v1` in the frontend GitHub secret.
2. Create a public S3 bucket (or enable signed URLs), apply `s3-cors.json` after
   replacing the domains, and fill all `AWS_*` values.
3. Copy this directory to `${VPS_APP_DIR}/deploy` and copy the repository-root
   `docker-compose.prod.yml` to `${VPS_APP_DIR}`.
4. Restore the current PostgreSQL dump as described below. Then run
   `docker compose run --rm backend python manage.py migrate --noinput` and
   `docker compose up -d`.
5. Verify `https://DOMAIN/api/v1/health/`, the admin, an image URL, and seeking
   in both the showreel and a project video.

This procedure is manual. The release workflow builds and publishes the backend
image to GHCR, but does not connect to a server. The server `.env` stays outside
Git and must be prepared before the first deployment.

## Moving the current content to production

The repository contains no seed content. PostgreSQL is the source of truth, so
create a custom-format dump from the current local database:

```powershell
docker compose exec postgres sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc --no-owner --no-acl -f /tmp/lumenary.dump'
docker compose cp postgres:/tmp/lumenary.dump ./lumenary.dump
```

Copy `lumenary.dump` to the VPS application directory. Start only PostgreSQL,
copy the dump into its container, restore it into the fresh empty database, and
then apply migrations from the deployed backend image:

```bash
docker compose -f docker-compose.prod.yml up -d postgres
docker compose -f docker-compose.prod.yml cp ./lumenary.dump postgres:/tmp/lumenary.dump
docker compose -f docker-compose.prod.yml exec postgres sh -c \
  'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner --no-acl \
  --exit-on-error /tmp/lumenary.dump'
docker compose -f docker-compose.prod.yml run --rm backend python manage.py migrate --noinput
```

A database dump stores media paths, not the file bytes. Copy the local `media/`
tree or mirror the current MinIO bucket into the production S3 bucket without
changing object keys. Verify the showreel, a project image, and a project video
before switching DNS. Keep the dump outside Git and delete the server copy after
the restore has been verified.

## Shared UNIX hosting

The frontend can be uploaded as the static contents of `dist/`. Backend deploy
must remain disabled until hoster.by confirms Python 3.12, a persistent WSGI
process, PostgreSQL, SSH/pip/venv access, and the application reload command.
If any of these are unavailable, use Cloud VPS for the backend and database.
