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
4. Run `docker compose pull`, `docker compose run --rm backend python manage.py
   migrate --noinput`, and `docker compose up -d`.
5. Verify `https://DOMAIN/api/v1/health/`, the admin, an image URL, and seeking
   in both the showreel and a project video.

GitHub Actions repeats steps 3-5 on every push to `main`. The VPS `.env` stays
on the server and is never committed. Required repository secrets are listed in
the root README.

## Shared UNIX hosting

The frontend can be uploaded as the static contents of `dist/`. Backend deploy
must remain disabled until hoster.by confirms Python 3.12, a persistent WSGI
process, PostgreSQL, SSH/pip/venv access, and the application reload command.
If any of these are unavailable, use Cloud VPS for the backend and database.
