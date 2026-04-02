from app.config import settings
from app.redis_dao.redis_client import RedisClient
from app.redis_dao.custom_redis import CustomRedis

redis_manager = RedisClient(host=settings.REDIS_HOST,
                            port=settings.REDIS_PORT,
                            password=settings.REDIS_PASSWORD,
                            ssl_flag=settings.REDIS_SSL)


async def get_redis() -> CustomRedis:
    """Функция зависимости для получения клиента Redis"""
    return redis_manager.get_client()
