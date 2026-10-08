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
docker compose up -d postgres minio minio-init
```

Перейдите в backend, создайте окружение и установите зависимости:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Подготовьте пустую базу:

```powershell
python manage.py migrate
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
Создайте и опубликуйте главную страницу, затем заполните тексты сайта, контакты,
услуги, проекты и аренду. Пока опубликованной главной страницы нет, frontend
показывает экран технической недоступности.

## Обычный запуск

Если первый запуск уже был сделан, обычно нужны только эти команды:

```powershell
cd D:\work\Lumenary-web
docker compose up -d postgres minio minio-init
cd backend
.\.venv\Scripts\Activate.ps1
python manage.py runserver 127.0.0.1:8000
```

## Где редактировать сайт

- `Главная`: первый экран, заголовок, текст, теги и showreel.
- `Услуги`: карточки услуг на главной.
- `Проекты`: категории, проекты, обложки и видео.
- `Аренда`: категории, подкатегории, позиции и характеристики.
- `Контакты`: email, телефон, адрес, соцсети и юридический текст футера.
- `Тексты сайта`: заголовки, описания страниц и призывы к действию.

Главная страница публикуется кнопкой `Опубликовать`. Проекты и позиции аренды
показываются на сайте только со статусом `Опубликовано`; новые записи создаются
черновиками. В настройках и справочниках достаточно нажать `Сохранить`.

Репозиторий не содержит стартового бизнес-контента. Единственный источник
содержимого сайта — PostgreSQL; перенос заполненного сайта выполняется дампом
базы, а изображения и видео переносятся отдельно в S3.

В полях showreel и видео проекта можно загрузить файл либо указать ссылку на
YouTube, Vimeo или прямую ссылку на MP4. Одновременно использовать файл и
ссылку нельзя.

## Production и S3

Основной вариант размещения — VPS/Cloud VPS с Docker Compose. Канонические
файлы, список секретов и инструкция первого запуска находятся в `deploy/` и
`.env.production.example`. Production требует внешнее S3-compatible хранилище:
после заполнения `AWS_*` все новые изображения и видео Wagtail загружает прямо
в bucket, а API возвращает публичный или подписанный URL.

На обычном UNIX shared hosting статический frontend можно загрузить отдельно.
Backend разворачивайте там только после подтверждения Python 3.12, постоянного
WSGI-процесса, PostgreSQL, SSH/pip/venv и команды перезапуска приложения.

GitHub Actions для VPS используют секреты `VPS_HOST`, `VPS_USER`,
`VPS_SSH_KEY`, `VPS_APP_DIR`, `APP_DOMAIN`, `GHCR_USERNAME` и `GHCR_TOKEN`.

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
