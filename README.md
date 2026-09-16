# Lumenary Backend

Backend - это админка и API сайта. Через него редактируются главная страница, услуги, проекты, каталог аренды, контакты и футер.

Локальные адреса:

- Админка: http://127.0.0.1:8000/admin/
- Документация API: http://127.0.0.1:8000/api/docs/
- Техническая схема API: http://127.0.0.1:8000/api/schema/

## Что установить один раз

1. Python 3.12 или новее: https://www.python.org/downloads/
2. Docker Desktop: https://www.docker.com/products/docker-desktop/
3. Git: https://git-scm.com/downloads

При установке Python включите галочку `Add python.exe to PATH`.

## Первый запуск

Откройте PowerShell в папке проекта:

```powershell
cd D:\work\Lumenary-web
```

Запустите базу данных и служебные контейнеры:

```powershell
docker compose up -d postgres redis minio
```

Перейдите в backend, создайте окружение и установите зависимости:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Подготовьте базу и стартовый контент:

```powershell
python manage.py migrate
python manage.py seed_figma_content
```

Создайте пользователя для входа в админку:

```powershell
python manage.py createsuperuser
```

Запустите backend:

```powershell
python manage.py runserver 127.0.0.1:8000
```

После запуска откройте http://127.0.0.1:8000/admin/ и войдите под созданным логином и паролем.

## Обычный запуск

Если первый запуск уже был сделан, обычно нужны только эти команды:

```powershell
cd D:\work\Lumenary-web
docker compose up -d postgres redis minio
cd backend
.\.venv\Scripts\Activate.ps1
python manage.py runserver 127.0.0.1:8000
```

## Где редактировать сайт

- `Страницы` -> главная страница: первый экран, заголовок, текст, теги, showreel.
- `Услуги`: карточки услуг на главной.
- `Портфолио`: категории и проекты.
- `Аренда`: категории, подкатегории, позиции и характеристики.
- `Настройки` -> тексты секций главной: заголовки основных блоков.
- `Настройки` -> контакты: email, телефон, адрес и соцсети.
- `Настройки` -> футер: реквизиты и дополнительный текст внизу сайта.

После редактирования страницы нажмите `Опубликовать`. В настройках и справочниках обычно достаточно нажать `Сохранить`.

## Проверка

Проверить, что backend настроен правильно:

```powershell
python manage.py check --database default
python manage.py makemigrations --check --dry-run
python manage.py spectacular --file openapi-check.yaml --validate
```

Запустить тесты:

```powershell
python manage.py test --settings=config.test_settings
```

Если тесты не могут создать тестовую базу, дайте пользователю PostgreSQL право создавать базы:

```sql
ALTER ROLE "Lumenary" CREATEDB;
```

## Если что-то не работает

- Docker Desktop должен быть открыт.
- Проверить контейнеры можно командой `docker compose ps`.
- Если PowerShell не видит `python`, переустановите Python с галочкой `Add python.exe to PATH`.
- Если порт `8000` занят, остановите старый backend или запустите временно так: `python manage.py runserver 127.0.0.1:8001`.
- Если frontend не получает данные, проверьте, что backend запущен именно на `http://127.0.0.1:8000/`.
