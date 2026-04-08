# Запуск EasyBooker

Стек: **Python 3.10+**, **FastAPI**, **aiogram 3**, **PostgreSQL**, **Redis** (для модулей кэша), **Alembic** для миграций.

## 1. Установка зависимостей

```bash
cd EasyBooker
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
python3 -m pip install -r requirements.txt
```

## 2. Переменные окружения

```bash
cp .env.example .env
# Отредактируйте .env: BOT_TOKEN, DB_*, BACK_URL, FRONT_URL, ADMINS
```

`BACK_URL` — публичный HTTPS-адрес, где доступен этот FastAPI-сервис (для вебхука Telegram: `POST /webhook`).

`FRONT_URL` — базовый URL фронтенда (мини-приложение), на который ссылается бот.

## 3. База данных и миграции

Поднимите PostgreSQL, создайте БД и пользователя. Затем:

```bash
# из корня репозитория, где лежит alembic.ini
alembic upgrade head
```

При необходимости проверьте `alembic.ini` и строку подключения в `app/config.py` / `.env`.

## 4. Redis

Запустите Redis локально или укажите хост/порт в `.env`. Поля `REDIS_*` заданы в `app/config.py` со значениями по умолчанию для локальной разработки.

## 5. Запуск сервера

```bash
# из корня репозитория, где лежит alembic.ini и папка app/
PYTHONPATH=. python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

При старте приложение выставляет webhook Telegram на `{BACK_URL}/webhook`.

## 6. Примечание о фронтенде

В репозитории — бэкенд и Telegram-бот. Отдельный фронтенд (WebApp) должен быть развёрнут отдельно и доступен по `FRONT_URL`;
