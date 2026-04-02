from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.dao.database import Base


class User(Base):
    """Модель пользователя системы."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    username: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    firstname: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    lastname: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    owner: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    users_autos: Mapped[list["UsersAutos"]] = relationship(
        "UsersAutos", back_populates="user", cascade="all, delete-orphan"
    )
    bookings: Mapped[list["Booking"]] = relationship(
        "Booking", back_populates="user", cascade="all, delete-orphan"
    )
    reviews: Mapped[list["Review"]] = relationship(
        "Review", back_populates="user", cascade="all, delete-orphan"
    )


class CarWash(Base):
    """Модель автомойки."""

    __tablename__ = "car_washes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)  # Название автомойки
    address: Mapped[str] = mapped_column(String, nullable=False)  # Адрес автомойки
    busy: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )  # Статус занятости
    latitude: Mapped[float] = mapped_column(Float, nullable=False)  # Широта
    longitude: Mapped[float] = mapped_column(Float, nullable=False)  # Долгота
    owner_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )  # ID владельца автомойки
    work_start: Mapped[str] = mapped_column(
        String, nullable=True
    )  # Время начала работы (HH:MM)
    work_end: Mapped[str] = mapped_column(
        String, nullable=True
    )  # Время окончания работы (HH:MM)
    work_days: Mapped[str] = mapped_column(
        String, nullable=True
    )  # Рабочие дни (пн,вт,ср,чт,пт,сб,вс)
    photo_url: Mapped[Optional[str]] = mapped_column(
        String, nullable=True
    )  # Ссылка на фото автомойки
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # Описание автомойки
    rating: Mapped[float] = mapped_column(
        Float, nullable=True, default=0.0, server_default=text("0.0")
    )
    token: Mapped[str] = mapped_column(
        String, nullable=True, server_default=func.gen_random_uuid()
    )  # Уникальный токен для автомойки

    services: Mapped[list["CarWashService"]] = relationship(
        "CarWashService", back_populates="car_wash", cascade="all, delete-orphan"
    )
    posts: Mapped[list["WashPost"]] = relationship(
        "WashPost", back_populates="car_wash", cascade="all, delete-orphan"
    )
    owner: Mapped[Optional["User"]] = relationship("User")
    bookings: Mapped[list["Booking"]] = relationship(
        "Booking", back_populates="car_wash", cascade="all, delete-orphan"
    )
    reviews: Mapped[list["Review"]] = relationship(
        "Review", back_populates="car_wash", cascade="all, delete-orphan"
    )


class Service(Base):
    """Модель услуги автомойки."""

    __tablename__ = "services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)  # Название услуги
    car_wash_services: Mapped[list["CarWashService"]] = relationship(
        "CarWashService", back_populates="service", cascade="all, delete-orphan"
    )


class CarWashService(Base):
    """Модель услуги конкретной автомойки."""

    __tablename__ = "car_wash_services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    car_wash_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("car_washes.id", ondelete="CASCADE"), nullable=False
    )
    service_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("services.id", ondelete="CASCADE"), nullable=False
    )
    price: Mapped[int] = mapped_column(Integer, nullable=False)  # Цена услуги
    duration: Mapped[int] = mapped_column(
        Integer, nullable=False
    )  # Продолжительность услуги в минутах

    # Связи с другими таблицами
    car_wash: Mapped["CarWash"] = relationship("CarWash", back_populates="services")
    service: Mapped["Service"] = relationship(
        "Service", back_populates="car_wash_services"
    )
    bookings: Mapped[list["Booking"]] = relationship(
        "Booking", back_populates="service", cascade="all, delete-orphan"
    )

    @property
    def service_name(self) -> str:
        """Возвращает название услуги."""
        return self.service.name if self.service else ""

    def to_dict(self, exclude_none: bool = False):
        """
        Преобразует объект модели в словарь.

        Args:
            exclude_none (bool): Исключать ли None значения из результата

        Returns:
            dict: Словарь с данными объекта
        """
        result = super().to_dict(exclude_none)
        # Не используем ленивую загрузку service, так как это может вызвать проблемы в асинхронном контексте
        # service_name будет загружаться отдельно через JOIN в запросе
        return result


class Brand(Base):
    """Модель марки автомобиля."""

    __tablename__ = "brands"

    id: Mapped[str] = mapped_column(
        String, primary_key=True
    )  # Уникальный идентификатор марки
    name: Mapped[str] = mapped_column(String, nullable=False)  # Название марки
    cyrillic_name: Mapped[Optional[str]] = mapped_column(
        String, nullable=True
    )  # Название на кириллице
    popular: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )  # Популярность марки
    country: Mapped[Optional[str]] = mapped_column(
        String, nullable=True
    )  # Страна производитель

    # Связь с моделями
    models: Mapped[list["Model"]] = relationship(
        "Model", back_populates="brand", cascade="all, delete-orphan"
    )
    users_autos: Mapped[list["UsersAutos"]] = relationship(
        "UsersAutos", back_populates="brand", cascade="all, delete-orphan"
    )


class Model(Base):
    """Модель автомобиля."""

    __tablename__ = "models"

    id: Mapped[str] = mapped_column(
        String, primary_key=True
    )  # Уникальный идентификатор модели
    name: Mapped[str] = mapped_column(String, nullable=False)  # Название модели
    cyrillic_name: Mapped[Optional[str]] = mapped_column(
        String, nullable=True
    )  # Название на кириллице
    class_: Mapped[Optional[str]] = mapped_column(
        "class", String, nullable=True
    )  # Класс автомобиля
    year_from: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # Год начала производства
    year_to: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # Год окончания производства
    wash_time: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # Время мойки
    wash_time_complex: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # Время мойки комплексное
    wash_tech: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # Время мойки техническое

    # Внешний ключ для связи с таблицей brands
    mark_id: Mapped[str] = mapped_column(
        String, ForeignKey("brands.id", ondelete="CASCADE"), nullable=False
    )

    # Связь с маркой
    brand: Mapped["Brand"] = relationship("Brand", back_populates="models")
    users_autos: Mapped[list["UsersAutos"]] = relationship(
        "UsersAutos", back_populates="model", cascade="all, delete-orphan"
    )


class UsersAutos(Base):
    """Модель для связи пользователей с автомобилями."""

    __tablename__ = "users_autos"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )  # Автоинкрементный ID записи
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )  # Связь с пользователем
    brand_id: Mapped[str] = mapped_column(
        String, ForeignKey("brands.id", ondelete="CASCADE"), nullable=False
    )  # Связь с маркой
    model_id: Mapped[str] = mapped_column(
        String, ForeignKey("models.id", ondelete="CASCADE"), nullable=False
    )  # Связь с моделью
    car_number: Mapped[str] = mapped_column(
        String, unique=False, nullable=True
    )  # Номер автомобиля

    # Связи с другими таблицами
    user: Mapped["User"] = relationship("User", back_populates="users_autos")
    brand: Mapped["Brand"] = relationship("Brand", back_populates="users_autos")
    model: Mapped["Model"] = relationship("Model", back_populates="users_autos")
    bookings: Mapped[list["Booking"]] = relationship(
        "Booking", back_populates="user_auto", cascade="all, delete-orphan"
    )


class WashPost(Base):
    """Модель поста автомойки."""

    __tablename__ = "wash_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    car_wash_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("car_washes.id", ondelete="CASCADE"), nullable=False
    )
    post_number: Mapped[int] = mapped_column(Integer, nullable=False)  # Номер поста
    is_open: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )  # Статус поста

    car_wash: Mapped["CarWash"] = relationship("CarWash", back_populates="posts")

    __table_args__ = (
        UniqueConstraint("car_wash_id", "post_number", name="uq_post_number"),
    )


class Booking(Base):
    """Модель бронирования автомойки."""

    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    car_wash_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("car_washes.id", ondelete="CASCADE"), nullable=False
    )
    service_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("car_wash_services.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    user_auto_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users_autos.id", ondelete="CASCADE"), nullable=False
    )
    post_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("wash_posts.id", ondelete="SET NULL"), nullable=True
    )  # Связь с постом автомойки
    booking_date: Mapped[str] = mapped_column(
        String, nullable=False
    )  # Дата брони (YYYY-MM-DD)
    booking_time: Mapped[str] = mapped_column(
        String, nullable=False
    )  # Время брони (HH:MM)
    status: Mapped[str] = mapped_column(
        String, nullable=False, default="pending"
    )  # Статус: pending, confirmed, cancelled, completed
    cancellation_reason: Mapped[Optional[str]] = mapped_column(
        String, nullable=True
    )  # Причина отмены
    price_at_booking: Mapped[int] = mapped_column(
        Integer, nullable=False
    )  # Цена услуги на момент брони

    # Связи с другими таблицами
    car_wash: Mapped["CarWash"] = relationship("CarWash", back_populates="bookings")
    service: Mapped["CarWashService"] = relationship(
        "CarWashService", back_populates="bookings"
    )
    user: Mapped["User"] = relationship("User", back_populates="bookings")
    user_auto: Mapped["UsersAutos"] = relationship(
        "UsersAutos", back_populates="bookings"
    )
    post: Mapped[Optional["WashPost"]] = relationship("WashPost", backref="bookings")


class Review(Base):
    """Модель отзывов для автомойки."""

    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    car_wash_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("car_washes.id", ondelete="CASCADE"), nullable=False
    )
    rating: Mapped[float] = mapped_column(Float, nullable=False)
    text: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )

    # Связи с другими таблицами
    user: Mapped["User"] = relationship("User", back_populates="reviews")
    car_wash: Mapped["CarWash"] = relationship("CarWash", back_populates="reviews")
