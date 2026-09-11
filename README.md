# Luminary Backend

Headless backend для сайта Luminary.

## Стек

- Django
- Django REST Framework
- Wagtail
- PostgreSQL
- Redis
- Celery
- S3-compatible storage

## Основная модель

- Wagtail управляет редакторскими страницами, контактами и футером.
- `projects` хранит проекты и detail-страницы портфолио-кейсов.
- `rental` хранит каталог аренды, дерево категорий, характеристики и поиск.
- `leads` хранит общие заявки и заявки по подборке аренды.
- `notifications` отправляет Telegram-уведомления через Celery.

## Быстрый старт

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Для PostgreSQL, Redis, S3 и Telegram см. `.env.example`.
