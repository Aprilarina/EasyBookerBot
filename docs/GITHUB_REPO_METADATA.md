# Настройки карточки репозитория на GitHub (About)

Файл для ручного заполнения: **Settings недоступны через git**, поля «About» задаются в веб-интерфейсе: репозиторий → шестерёнка **About** → **Edit repository details**.

## Description (описание, одна строка)

```
Telegram bot и FastAPI: бронирование автомойки. Aiogram 3, PostgreSQL, Redis. MIT. Бот: @easybooker_bot
```

## Website

```
https://t.me/easybooker_bot
```

*(Альтернатива: ссылка на Holst-документацию — см. README.)*

## Topics (метки)

Вставьте по одной или через запятую (GitHub подскажет):

`telegram-bot` `fastapi` `aiogram` `python` `postgresql` `redis` `sqlalchemy` `alembic` `telegram-mini-apps` `booking` `car-wash` `mit` `opensource`

## После первого push

- Вкладка **Actions** — убедитесь, что workflow **CI** прошёл (зелёная галочка на коммите).
- **Settings → General → Features** — при желании включите **Wikis** / **Discussions** (не обязательно).

Dependabot подхватит `.github/dependabot.yml` автоматически; PR с обновлениями зависимостей могут появиться в течение недели.
