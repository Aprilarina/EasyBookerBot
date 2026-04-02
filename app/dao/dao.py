from loguru import logger
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload

from app.dao.base import BaseDAO
from app.dao.models import (
    Booking,
    Brand,
    CarWash,
    CarWashService,
    Model,
    Review,
    Service,
    User,
    UsersAutos,
    WashPost,
)


class ReviewDAO(BaseDAO):
    model = Review


class BookingDAO(BaseDAO):
    model = Booking

    async def get_booking_full_info(self, booking_id: int):
        """
        Получает полную информацию о брони с учетом всех зависимостей.

        Args:
            booking_id: ID брони

        Returns:
            dict: Словарь с полной информацией о брони и связанными данными
        """

        query = (
            select(self.model)
            .options(
                joinedload(self.model.car_wash),
                joinedload(self.model.service).joinedload(CarWashService.service),
                joinedload(self.model.user),
                joinedload(self.model.user_auto).joinedload(UsersAutos.brand),
                joinedload(self.model.user_auto).joinedload(UsersAutos.model),
                joinedload(self.model.post),
            )
            .where(self.model.id == booking_id)
        )

        result = await self._session.execute(query)
        booking = result.scalars().first()

        if not booking:
            return None

        return {
            "id": booking.id,
            "car_wash": {
                "id": booking.car_wash.id,
                "name": booking.car_wash.name,
                "address": booking.car_wash.address,
                "admin_id": booking.car_wash.owner_id,
            },
            "service": {
                "id": booking.service.id,
                "name": booking.service.service.name,
                "price": booking.price_at_booking,
            },
            "user": {
                "id": booking.user.id,
                "telegram_id": booking.user.telegram_id,
                "username": booking.user.username,
                "firstname": booking.user.firstname,
                "lastname": booking.user.lastname,
            },
            "user_auto": {
                "id": booking.user_auto.id,
                "car_number": booking.user_auto.car_number,
                "brand": {
                    "id": booking.user_auto.brand.id,
                    "name": booking.user_auto.brand.name,
                },
                "model": {
                    "id": booking.user_auto.model.id,
                    "name": booking.user_auto.model.name,
                },
            },
            "post": (
                {"id": booking.post.id, "post_number": booking.post.post_number}
                if booking.post
                else None
            ),
            "booking_date": booking.booking_date,
            "booking_time": booking.booking_time,
            "status": booking.status,
            "cancellation_reason": booking.cancellation_reason,
        }

    async def get_carwash_statistics(self, car_wash_id: int):
        """
        Получает статистику по всем броням конкретной автомойки.

        Args:
            car_wash_id: ID автомойки

        Returns:
            dict: Словарь со статистикой
        """
        query = (
            select(self.model)
            .options(
                joinedload(self.model.car_wash),
                joinedload(self.model.service).joinedload(CarWashService.service),
                joinedload(self.model.user),
                joinedload(self.model.user_auto).joinedload(UsersAutos.brand),
                joinedload(self.model.user_auto).joinedload(UsersAutos.model),
                joinedload(self.model.post),
            )
            .where(self.model.car_wash_id == car_wash_id)
        )

        result = await self._session.execute(query)
        bookings = result.scalars().all()

        if not bookings:
            return None

        total_bookings = len(bookings)
        status_counts = {}
        total_revenue = 0

        for booking in bookings:
            status = booking.status
            status_counts[status] = status_counts.get(status, 0) + 1
            if status in ["confirmed", "completed"]:
                total_revenue += booking.price_at_booking

        return {
            "total_bookings": total_bookings,
            "status_counts": status_counts,
            "total_revenue": total_revenue,
            "bookings": [
                {
                    "id": booking.id,
                    "car_wash": {
                        "id": booking.car_wash.id,
                        "name": booking.car_wash.name,
                        "address": booking.car_wash.address,
                    },
                    "service": {
                        "id": booking.service.id,
                        "name": booking.service.service.name,
                        "price": booking.price_at_booking,
                    },
                    "user": {
                        "id": booking.user.id,
                        "telegram_id": booking.user.telegram_id,
                        "username": booking.user.username,
                        "firstname": booking.user.firstname,
                        "lastname": booking.user.lastname,
                    },
                    "user_auto": {
                        "id": booking.user_auto.id,
                        "car_number": booking.user_auto.car_number,
                        "brand": {
                            "id": booking.user_auto.brand.id,
                            "name": booking.user_auto.brand.name,
                        },
                        "model": {
                            "id": booking.user_auto.model.id,
                            "name": booking.user_auto.model.name,
                        },
                    },
                    "post": (
                        {"id": booking.post.id, "post_number": booking.post.post_number}
                        if booking.post
                        else None
                    ),
                    "booking_date": booking.booking_date,
                    "booking_time": booking.booking_time,
                    "status": booking.status,
                    "cancellation_reason": booking.cancellation_reason,
                }
                for booking in bookings
            ],
        }

    async def get_carwash_active_bookings(self, car_wash_id: int):
        """
        Получает активные брони (pending и confirmed) для конкретной автомойки.

        Args:
            car_wash_id: ID автомойки

        Returns:
            list: Список активных броней
        """
        # Обновляем сессию перед запросом
        self._session.expire_all()

        query = (
            select(self.model)
            .options(
                joinedload(self.model.car_wash),
                joinedload(self.model.service).joinedload(CarWashService.service),
                joinedload(self.model.user),
                joinedload(self.model.user_auto).joinedload(UsersAutos.brand),
                joinedload(self.model.user_auto).joinedload(UsersAutos.model),
                joinedload(self.model.post),
            )
            .where(
                self.model.car_wash_id == car_wash_id,
                self.model.status.in_(["pending", "confirmed"]),
            )
        )

        result = await self._session.execute(query)
        bookings = result.scalars().all()

        if not bookings:
            return []

        return [
            {
                "id": booking.id,
                "car_wash": {
                    "id": booking.car_wash.id,
                    "name": booking.car_wash.name,
                    "address": booking.car_wash.address,
                },
                "service": {
                    "id": booking.service.id,
                    "name": booking.service.service.name,
                    "price": booking.price_at_booking,
                },
                "user": {
                    "id": booking.user.id,
                    "telegram_id": booking.user.telegram_id,
                    "username": booking.user.username,
                    "firstname": booking.user.firstname,
                    "lastname": booking.user.lastname,
                },
                "user_auto": {
                    "id": booking.user_auto.id,
                    "car_number": booking.user_auto.car_number,
                    "brand": {
                        "id": booking.user_auto.brand.id,
                        "name": booking.user_auto.brand.name,
                    },
                    "model": {
                        "id": booking.user_auto.model.id,
                        "name": booking.user_auto.model.name,
                    },
                },
                "post": (
                    {"id": booking.post.id, "post_number": booking.post.post_number}
                    if booking.post
                    else None
                ),
                "booking_date": booking.booking_date,
                "booking_time": booking.booking_time,
                "status": booking.status,
                "cancellation_reason": booking.cancellation_reason,
            }
            for booking in bookings
        ]

    async def get_user_bookings_full_info(self, user_id: int):
        """
        Получает полную информацию о всех бронях пользователя с учетом всех зависимостей.

        Args:
            user_id: ID пользователя

        Returns:
            list: Список словарей с полной информацией о бронях и связанными данными
        """
        query = (
            select(self.model)
            .options(
                joinedload(self.model.car_wash),
                joinedload(self.model.service).joinedload(CarWashService.service),
                joinedload(self.model.user),
                joinedload(self.model.user_auto).joinedload(UsersAutos.brand),
                joinedload(self.model.user_auto).joinedload(UsersAutos.model),
                joinedload(self.model.post),
            )
            .where(self.model.user_id == user_id)
        )

        result = await self._session.execute(query)
        bookings = result.scalars().all()

        if not bookings:
            return []

        bookings_info = []
        for booking in bookings:
            bookings_info.append(
                {
                    "id": booking.id,
                    "car_wash": {
                        "id": booking.car_wash.id,
                        "name": booking.car_wash.name,
                        "address": booking.car_wash.address,
                    },
                    "service": {
                        "id": booking.service.id,
                        "name": booking.service.service.name,
                        "price": booking.price_at_booking,
                    },
                    "user": {
                        "id": booking.user.id,
                        "telegram_id": booking.user.telegram_id,
                        "username": booking.user.username,
                        "firstname": booking.user.firstname,
                        "lastname": booking.user.lastname,
                    },
                    "user_auto": {
                        "id": booking.user_auto.id,
                        "car_number": booking.user_auto.car_number,
                        "brand": {
                            "id": booking.user_auto.brand.id,
                            "name": booking.user_auto.brand.name,
                        },
                        "model": {
                            "id": booking.user_auto.model.id,
                            "name": booking.user_auto.model.name,
                        },
                    },
                    "post": (
                        {"id": booking.post.id, "post_number": booking.post.post_number}
                        if booking.post
                        else None
                    ),
                    "booking_date": booking.booking_date,
                    "booking_time": booking.booking_time,
                    "status": booking.status,
                    "cancellation_reason": booking.cancellation_reason,
                }
            )

        return bookings_info

    async def find_all_with_relations(self, filters: BaseModel, relations: list[str]):
        """
        Получает все записи с загрузкой связанных данных.

        Args:
            filters: Фильтры для поиска
            relations: Список путей к связанным данным (например, ["service.service", "user_auto.brand"])

        Returns:
            list: Список записей с загруженными связанными данными
        """
        query = select(self.model)

        # Добавляем загрузку связанных данных
        for relation in relations:
            parts = relation.split(".")
            current = self.model
            for part in parts:
                current = getattr(current, part)
            query = query.options(selectinload(current))

        # Добавляем фильтры
        for field, value in filters.model_dump().items():
            if value is not None:
                query = query.where(getattr(self.model, field) == value)

        result = await self._session.execute(query)
        return result.scalars().all()


class WashPostDAO(BaseDAO):
    model = WashPost


class UserDAO(BaseDAO):
    model = User

    async def get_user_info_by_telegram_id(self, telegram_id: int) -> User | None:
        query = select(self.model).filter_by(telegram_id=telegram_id)
        result = await self._session.execute(query)
        record = result.scalar_one_or_none()
        log_message = f"Запись {self.model.__name__} с ID {telegram_id} {'найдена' if record else 'не найдена'}."
        logger.info(log_message)
        return record


class BrandDAO(BaseDAO):
    model = Brand


class ModelDAO(BaseDAO):
    model = Model


class UsersAutosDAO(BaseDAO):
    model = UsersAutos


class CarWashDAO(BaseDAO):
    model = CarWash


class ServiceDAO(BaseDAO):
    model = Service


class CarWashServiceDAO(BaseDAO):
    model = CarWashService

    async def find_all_with_service(self, filters: BaseModel | None = None):
        """
        Получает все услуги автомойки с загруженными названиями услуг через JOIN.

        Args:
            filters: Фильтры для поиска

        Returns:
            list: Список услуг автомойки с названиями
        """
        from sqlalchemy import select
        from sqlalchemy.orm import joinedload

        filter_dict = filters.model_dump(exclude_unset=True) if filters else {}
        query = (
            select(self.model)
            .options(joinedload(self.model.service))
            .filter_by(**filter_dict)
        )
        result = await self._session.execute(query)
        return result.scalars().unique().all()
        return result.scalars().unique().all()
        return result.scalars().unique().all()
        return result.scalars().unique().all()
