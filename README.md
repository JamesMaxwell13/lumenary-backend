# Lumenary Backend

Django/Wagtail CMS, REST API и конфигурация общего VPS-стека Lumenary.
PostgreSQL хранит контент, MinIO — изображения и загруженные видео.

## Стек

- Python 3.12, Django, Wagtail, Django REST Framework
- PostgreSQL 16
- MinIO через S3 API
- Docker Compose
- frontend/nginx как единая публичная точка входа

## Локальная разработка

Из корня `Lumenary-web`:

```powershell
docker compose up -d postgres minio minio-init
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 127.0.0.1:8000
```

- Админка: <http://127.0.0.1:8000/admin/>
- OpenAPI: <http://127.0.0.1:8000/api/docs/>
- Health check: <http://127.0.0.1:8000/api/v1/health/>

## Контент

Актуальные тексты находятся в PostgreSQL, стартового бизнес-контента в
репозитории нет. Основное меню Wagtail:

- `Главная` — hero, навигация и showreel;
- `Услуги` — карточки услуг;
- `Проекты` — проекты и разделы;
- `Аренда` — позиции, разделы и характеристики;
- `Контакты` — контакты и футер;
- `Заголовки` — заголовки страниц, описания и CTA.

Видео поддерживают загруженный файл, прямой MP4 URL, YouTube и Vimeo.

## Проверки

```powershell
python manage.py check --database default
python manage.py makemigrations --check --dry-run
python manage.py spectacular --file openapi-check.yaml --validate
python manage.py test --settings=config.test_settings
```

## VPS-архитектура

`docker-compose.prod.yml` содержит ровно четыре сервиса:

| Сервис | Назначение | Публичные порты |
| --- | --- | --- |
| `postgres` | база данных | нет |
| `minio` | S3-compatible media storage | только console на `127.0.0.1:9001` |
| `backend` | Wagtail и API | нет |
| `frontend` | React, nginx, reverse proxy и TLS | `80`, `443` |

Инициализация bucket выполняется временным запуском backend-команды и не создаёт
пятый постоянный сервис.

## Первый запуск на Ubuntu VPS

Установите Docker Engine, Compose plugin, Git и curl. Certbot нужен только после
подключения публичного домена.

```bash
sudo usermod -aG docker "$USER"
sudo mkdir -p /opt/lumenary
sudo chown "$USER":"$USER" /opt/lumenary
git clone https://github.com/JamesMaxwell13/lumenary-backend.git /opt/lumenary
cd /opt/lumenary
cp .env.production.example .env
chmod 600 .env
```

Заполните `.env`: IP VM, образы GHCR, Django secret, пароли PostgreSQL и MinIO.
Для приватных образов выполните один раз:

```bash
echo "GHCR_PAT" | docker login ghcr.io -u "GITHUB_USERNAME" --password-stdin
```

PAT должен иметь scope `read:packages`. Первый и последующие деплои выполняются
одинаково:

```bash
cd /opt/lumenary
./scripts/vps-update.sh
```

Скрипт получает изменения конфигурации, скачивает образы, поднимает PostgreSQL и
MinIO, создаёт bucket, сохраняет dump базы, применяет миграции и обновляет
backend/frontend. Миграции выполняются до замены работающего backend.

## Управление

```bash
./scripts/vps-status.sh
./scripts/vps-backup.sh
./scripts/vps-restore.sh backups/lumenary-YYYYMMDDTHHMMSSZ.dump --yes
docker compose --env-file .env -f docker-compose.prod.yml logs -f backend
```

Для rollback укажите в `.env` SHA-теги `BACKEND_IMAGE` и `FRONTEND_IMAGE`, затем
повторите `vps-update.sh`.

MinIO console доступна через SSH tunnel:

```bash
ssh -L 9001:127.0.0.1:9001 user@vps
```

После этого откройте <http://127.0.0.1:9001/>.

## HTTPS

Для локальной VM оставьте `ENABLE_HTTPS=false`, укажите IP в `SITE_HOST` и HTTP
адреса в Django/S3 настройках.

После направления публичного домена на VPS установите Certbot, замените IP на
домен в `.env` и выполните:

```bash
sudo ./scripts/vps-enable-https.sh
```

Для автоматического продления добавьте в root crontab:

```cron
17 3 * * * /opt/lumenary/scripts/vps-renew-certificates.sh
```

Сертификаты и challenge-файлы хранятся в `/opt/lumenary/certbot` и подключаются к
frontend-контейнеру read-only.

## Перенос контента

Перенесите PostgreSQL через custom-format `pg_dump` и восстановите
`vps-restore.sh`. Дамп содержит пути к медиа, но не сами объекты. Содержимое
текущего MinIO bucket нужно зеркалировать отдельно с сохранением object keys.

## CI/CD

Push в `main` запускает тесты, собирает backend-образ и публикует в GHCR теги
commit SHA и `main`. Workflow не подключается к VPS; обновление запускается
локальной командой на VM.
