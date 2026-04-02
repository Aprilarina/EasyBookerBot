# EasyBooker

Telegram-бот и HTTP API для записи на услуги автомоек: бронирование, роли пользователя и администратора, интеграция с веб-приложением (мини-приложение Telegram).

**Репозиторий:** [github.com/Aprilarina/EasyBookerBot](https://github.com/Aprilarina/EasyBookerBot)

## Рабочий бот в Telegram

Публичный бот **работает** и доступен в Telegram: **[@easybooker_bot](https://t.me/easybooker_bot)**

## Лицензия и авторство

Проект распространяется под лицензией **MIT** — см. файл [`LICENSE`](LICENSE).

Сервис EasyBooker создан по техническому заданию заказчика (правообладателя). Исходный код изначально разрабатывался в репозитории [Yakvenalex/EasyBookerBot](https://github.com/Yakvenalex/EasyBookerBot); правообладатель публикует открытую копию для сообщества.

## Документация

| Ресурс | Ссылка |
|--------|--------|
| Продуктовая документация (Holst) | [app.holst.so — EasyBooker](https://app.holst.so/share/b/e9f74409-db54-4fca-b19b-796eff42a3ad) |
| Запуск и окружение | [docs/SETUP.md](docs/SETUP.md) |
| Происхождение кода | [docs/ATTRIBUTION.md](docs/ATTRIBUTION.md) |
| Публикация на GitHub | [docs/GITHUB_PUBLISH.md](docs/GITHUB_PUBLISH.md) |

## Структура репозитория

```
EasyBooker/
├── app/                 # Приложение FastAPI, aiogram, DAO, миграции Alembic
├── docs/                # Документация репозитория
├── alembic.ini
├── requirements.txt
├── .env.example         # Шаблон переменных окружения (скопируйте в .env)
└── LICENSE
```

## Быстрый старт

1. Склонируйте репозиторий и создайте виртуальное окружение.
2. `cp .env.example .env` и заполните секреты (`BOT_TOKEN`, PostgreSQL, `BACK_URL`, `FRONT_URL`, `ADMINS`).
3. Примените миграции: `alembic upgrade head`.
4. Запустите: `PYTHONPATH=. python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000`

Подробности — в [docs/SETUP.md](docs/SETUP.md).

## Безопасность

Не коммитьте файл `.env` и токены бота. В репозитории есть только `.env.example`.

## Важно

Открытая публикация не подразумевает коммерческой поддержки или гарантии работоспособности во всех окружениях; используйте код на свой страх и риск (см. текст лицензии MIT).

В исходной выгрузке нет каталога `app/templates/` (при этом `app/api/router.py` ссылается на Jinja2-шаблоны). Если при развёртывании не хватает шаблонов, восстановите их из рабочего бэка или уточните у автора исходного репозитория; фронтенд WebApp разворачивается отдельно по `FRONT_URL`.
