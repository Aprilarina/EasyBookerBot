# Как опубликовать репозиторий на GitHub

Локально уже выполнены `git init` и первый коммит в каталоге `EasyBooker/`. Осталось создать пустой репозиторий на GitHub и отправить код.

## Вариант A: веб-интерфейс

1. Войдите на [github.com/new](https://github.com/new).
2. Имя репозитория, например: **EasyBooker**.
3. Репозиторий **публичный**, **без** README / .gitignore / лицензии (они уже есть локально).
4. После создания выполните в терминале (подставьте свой логин и имя репозитория):

```bash
cd /path/to/EasyBooker
git remote add origin https://github.com/<YOUR_USER>/EasyBooker.git
git push -u origin main
```

## Вариант B: GitHub CLI (`gh`)

Если установлен [GitHub CLI](https://cli.github.com/) и выполнен `gh auth login`:

```bash
cd /path/to/EasyBooker
gh repo create EasyBooker --public --source=. --remote=origin --push
```

## Примечание

Каталог `EasyBooker/` добавлен в `.gitignore` родительского репозитория `telegram-finance-bot`, чтобы не смешивать два проекта. Пуш делайте **только из** `EasyBooker/` в отдельный репозиторий на GitHub.
