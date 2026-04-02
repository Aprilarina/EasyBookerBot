from contextlib import asynccontextmanager

from aiogram.types import Update
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

from app.api.router import router as api_router
from app.config import settings
from app.tg_bot.admin.router import router as admin_router
from app.tg_bot.create_bot import bot, dp, start_bot, stop_bot
from app.tg_bot.start.router import router as start_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting bot setup...")
    dp.include_router(start_router)
    dp.include_router(admin_router)
    await start_bot()
    webhook_url = settings.get_webhook_url()
    await bot.set_webhook(
        url=webhook_url,
        allowed_updates=dp.resolve_used_update_types(),
        drop_pending_updates=True,
    )
    logger.success(f"Webhook set to {webhook_url}")
    yield
    logger.info("Shutting down bot...")
    # await bot.delete_webhook()
    await stop_bot()
    # logger.info("Webhook deleted")


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/static"), "static")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/webhook")
async def webhook(request: Request) -> None:
    logger.info("Received webhook request")
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)
    logger.info("Update processed")


app.include_router(api_router)
