# Lumenary Backend

Headless backend для сайта Lumenary.

## Стек

- Django
- Django REST Framework
- Wagtail
- PostgreSQL
- Redis
- Celery
- S3-compatible storage

## Основная модель

- `cms` хранит первый экран главной страницы, тексты секций, контакты и футер.
- `services` хранит карточки услуг.
- `projects` хранит портфолио и detail-страницы кейсов.
- `rental` хранит каталог аренды: разделы, подразделы, позиции и поиск.
- `leads` и `notifications` оставлены в кодовой базе как будущий отключенный модуль обращений, но сейчас не подключаются в `INSTALLED_APPS` и не имеют публичных endpoints.

## Быстрый старт

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_figma_content
python manage.py runserver
```

Для запуска всего проекта из корня используйте `make dev`.

## Redis

Локальный Redis описан в корневом `docker-compose.yml`.

- `REDIS_URL` / `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` используют DB `0` для Celery.
- `CACHE_URL` использует DB `1` для Django cache.
- Если `CACHE_URL` пустой, backend использует in-memory cache для локальной разработки.

## Админка Wagtail

Главная страница в меню админки ведет прямо на редактирование первого экрана из Figma: название продакшена, описание, теги и showreel.

Остальные части лендинга лежат рядом:

- `Услуги` — карточки услуг.
- `Портфолио` — проекты и разделы проектов.
- `Аренда` — разделы, подразделы и позиции аренды.
- `Настройки` — тексты секций главной, контакты и футер.
