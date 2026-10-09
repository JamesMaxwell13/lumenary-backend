# Lumenary Backend

Django/Wagtail CMS и REST API для сайта Lumenary. PostgreSQL является источником
контента; изображения и загруженные видео хранятся локально в разработке или в
S3-compatible storage в production.

## Стек

- Python 3.12, Django, Wagtail, Django REST Framework
- PostgreSQL 16
- django-storages и S3-compatible object storage
- Gunicorn, Docker и Docker Compose для контейнерного размещения

## Локальное окружение

Из корня `Lumenary-web` запустите PostgreSQL и MinIO:

```powershell
docker compose up -d postgres minio minio-init
```

Подготовьте backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 127.0.0.1:8000
```

Основные адреса:

- Wagtail: <http://127.0.0.1:8000/admin/>
- OpenAPI UI: <http://127.0.0.1:8000/api/docs/>
- OpenAPI schema: <http://127.0.0.1:8000/api/schema/>
- Health check: <http://127.0.0.1:8000/api/v1/health/>

## Конфигурация

`.env.example` содержит локальные значения, а `.env.production.example` — полный
production-шаблон. Файлы `.env` не коммитятся.

Ключевые группы переменных:

| Группа | Переменные |
| --- | --- |
| Django | `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, `CORS_ALLOWED_ORIGINS`, `ADMIN_BASE_URL` |
| PostgreSQL | `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT` |
| S3 | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_STORAGE_BUCKET_NAME`, `AWS_S3_ENDPOINT_URL`, `AWS_S3_PUBLIC_URL` и остальные `AWS_*` |
| Security | `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_SSL_REDIRECT`, `SECURE_HSTS_*` |
| Runtime | `CACHE_URL`, `GUNICORN_WORKERS`, `GUNICORN_TIMEOUT` |

При пустом `AWS_STORAGE_BUCKET_NAME` используется файловое хранилище `media/`.
При заполненном bucket все новые изображения и видео записываются в S3.

## Контент и админка

Основное меню Wagtail соответствует структуре сайта:

- `Главная` — hero, навигационные подписи, обложка и showreel;
- `Услуги` — прямой переход к списку карточек услуг;
- `Проекты` — проекты и их разделы;
- `Аренда` — позиции, разделы и характеристики;
- `Контакты` — контакты, соцсети и текст футера;
- `Заголовки` — заголовки, описания страниц и CTA.

Главная страница публикуется через Wagtail. Проекты и позиции аренды появляются в
публичном API только в опубликованном статусе. Репозиторий не содержит seed с
бизнес-контентом: актуальные тексты и записи находятся в PostgreSQL.

Showreel и видео проекта принимают один из источников: загруженный файл, прямую
MP4-ссылку, YouTube или Vimeo. Одновременное заполнение файла и URL запрещено
валидацией модели.

## Проверки

```powershell
python manage.py check --database default
python manage.py makemigrations --check --dry-run
python manage.py spectacular --file openapi-check.yaml --validate
python manage.py test --settings=config.test_settings
```

Тестовому пользователю PostgreSQL нужно право `CREATEDB`. Для локальной роли:

```sql
ALTER ROLE "Lumenary" CREATEDB;
```

## Production и перенос данных

Docker-образ собирается из корня backend. Контейнерный стек описан в
`docker-compose.prod.yml`, а Caddy и операции переноса — в `deploy/README.md`.

PostgreSQL dump переносит записи и пути к медиа, но не сами объекты. Базу нужно
переносить через `pg_dump`/`pg_restore`, а содержимое локального `media/` или MinIO
зеркалировать в production bucket с сохранением ключей объектов.

Обычный UNIX shared hosting пригоден для backend только при наличии Python 3.12,
PostgreSQL, постоянного WSGI-процесса, SSH/pip/venv и документированной команды
перезапуска приложения. До подтверждения этих возможностей автоматический deploy
backend отключён.

## CI/CD

`.github/workflows/release.yml` на push в `main` и при ручном запуске:

1. устанавливает зависимости;
2. выполняет Django checks, проверку миграций и тесты;
3. собирает Docker-образ;
4. публикует его в GHCR с тегами commit SHA и `main`.

Публикация использует встроенный `GITHUB_TOKEN`; дополнительные GHCR credentials и
VPS secrets не требуются. Workflow не разворачивает backend на UNIX-хостинге.
