# EasyBooker

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![CI](https://github.com/Aprilarina/EasyBookerBot/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Aprilarina/EasyBookerBot/actions/workflows/ci.yml)

Telegram-бот и HTTP API для записи на услуги автомоек: бронирование, роли пользователя и администратора, интеграция с веб-приложением (мини-приложение Telegram).

**Репозиторий:** [github.com/Aprilarina/EasyBookerBot](https://github.com/Aprilarina/EasyBookerBot)

## Рабочий бот в Telegram

Публичный бот **работает** и доступен в Telegram: **[@easybooker_bot](https://t.me/easybooker_bot)**

## Лицензия и авторство

Проект распространяется под лицензией **MIT** — см. файл [`LICENSE`](LICENSE).

## Документация

| Ресурс | Ссылка |
|--------|--------|
| **Discovery: сценарии, SWOT, рынок, ТЗ** | [docs/discovery/](docs/discovery/EASYBOOKER_DISCOVERY.md) |
| Запуск и окружение | [docs/SETUP.md](docs/SETUP.md) |
| Происхождение кода | [docs/ATTRIBUTION.md](docs/ATTRIBUTION.md) |
| Публикация на GitHub | [docs/GITHUB_PUBLISH.md](docs/GITHUB_PUBLISH.md) |

## Участие и безопасность

| Документ | Назначение |
|----------|------------|
| [CONTRIBUTING.md](CONTRIBUTING.md) | Как предлагать PR и issues |
| [SECURITY.md](SECURITY.md) | Как сообщить об уязвимости приватно |

## Структура репозитория

```
EasyBooker/
├── app/                 # FastAPI, aiogram, DAO, миграции Alembic
├── docs/                # Документация
├── .github/             # CI, Dependabot, шаблоны Issues / PR
├── alembic.ini
├── requirements.txt
├── .env.example
├── CONTRIBUTING.md
├── SECURITY.md
└── LICENSE
```

## Быстрый старт

1. Склонируйте репозиторий и создайте виртуальное окружение.
2. `cp .env.example .env` и заполните секреты (`BOT_TOKEN`, PostgreSQL, `BACK_URL`, `FRONT_URL`, `ADMINS`).
3. Примените миграции: `alembic upgrade head`.
4. Запустите: `PYTHONPATH=. python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000`

Подробности — в [docs/SETUP.md](docs/SETUP.md).

## Безопасность

Не коммитьте файл `.env` и токены бота. В репозитории есть только `.env.example`. См. [SECURITY.md](SECURITY.md).

## Важно

Открытая публикация не подразумевает коммерческой поддержки или гарантии работоспособности во всех окружениях; используйте код на свой страх и риск (см. текст лицензии MIT).

В исходной выгрузке нет каталога `app/templates/` (при этом `app/api/router.py` ссылается на Jinja2-шаблоны). Если при развёртывании не хватает шаблонов, восстановите их из рабочего бэка или уточните у автора исходного репозитория; фронтенд WebApp разворачивается отдельно по `FRONT_URL`.
