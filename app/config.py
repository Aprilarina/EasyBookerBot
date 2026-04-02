import os
from typing import List

from loguru import logger
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    FORMAT_LOG: str = "{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}"
    LOG_ROTATION: str = "10 MB"
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    BOT_TOKEN: str
    ADMINS: List[int]
    BACK_URL: str
    FRONT_URL: str
    REDIS_HOST: str = "127.0.0.1"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_SSL: bool = False
    STATIC_DIR: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

    def get_webhook_url(self) -> str:
        """Возвращает URL вебхука"""
        return f"{self.BACK_URL}/webhook"

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
    )


# Получаем параметры для загрузки переменных среды
settings = Settings()


def get_db_url():
    return (
        f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}@"
        f"{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    )


db_url = get_db_url()
log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "log.txt")
logger.add(
    log_file_path,
    format=settings.FORMAT_LOG,
    level="INFO",
    rotation=settings.LOG_ROTATION,
)


# Словарь для преобразования статусов
status_mapping = {
    "pending": "В обработке",
    "confirmed": "Подтверждено",
    "admin_rejected": "Отменено автомойкой",
    "user_rejected": "Отменено вами",
    "completed": "Завершено",
}
