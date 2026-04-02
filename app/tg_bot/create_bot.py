from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeDefault
from loguru import logger

from app.config import settings
from app.dao.database_middleware import (
    DatabaseMiddlewareWithCommit,
    DatabaseMiddlewareWithoutCommit,
)

bot = Bot(
    token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher(storage=MemoryStorage())
admins = settings.ADMINS


async def set_commands():
    commands = [BotCommand(command="start", description="Старт")]
    await bot.set_my_commands(commands, BotCommandScopeDefault())


# Функция, которая выполнится когда бот запустится
async def start_bot():
    dp.message.middleware.register(DatabaseMiddlewareWithoutCommit())
    dp.message.middleware.register(DatabaseMiddlewareWithCommit())
    dp.callback_query.middleware.register(DatabaseMiddlewareWithoutCommit())
    dp.callback_query.middleware.register(DatabaseMiddlewareWithCommit())
    await set_commands()
    for admin_id in settings.ADMINS:
        try:
            await bot.send_message(admin_id, "Я запущен🥳.")
        except Exception:
            pass
    logger.info("Бот успешно запущен.")


# Функция, которая выполнится когда бот завершит свою работу
async def stop_bot():
    try:
        for admin_id in settings.ADMINS:
            await bot.send_message(admin_id, "Бот остановлен. За что?😔")
    except:
        pass
    logger.error("Бот остановлен!")
