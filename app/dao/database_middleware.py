from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message
from loguru import logger

from app.dao.database import async_session_maker


class BaseDatabaseMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        session = None
        try:
            session = async_session_maker()
            self.set_session(data, session)
            result = await handler(event, data)
            await self.after_handler(session)
            return result
        except Exception as e:
            if session:
                await session.rollback()
            logger.error(f"Database error in middleware: {e}")
            raise e
        finally:
            if session:
                await session.close()

    def set_session(self, data: Dict[str, Any], session) -> None:
        """Метод для установки сессии в словарь данных."""
        raise NotImplementedError("Этот метод должен быть реализован в подклассах.")

    async def after_handler(self, session) -> None:
        """Метод для выполнения действий после вызова хендлера (например, коммит)."""
        pass


class DatabaseMiddlewareWithoutCommit(BaseDatabaseMiddleware):
    def set_session(self, data: Dict[str, Any], session) -> None:
        data["session_without_commit"] = session


class DatabaseMiddlewareWithCommit(BaseDatabaseMiddleware):
    def set_session(self, data: Dict[str, Any], session) -> None:
        data["session_with_commit"] = session

    async def after_handler(self, session) -> None:
        try:
            await session.commit()
        except Exception as e:
            logger.error(f"Error committing transaction: {e}")
            await session.rollback()
            raise e
