from aiogram.types import InlineKeyboardMarkup, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.config import settings
from app.dao.models import CarWash


def admin_main_keyboard(
    car_wash_data: list[CarWash], user_id: int = 2
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for car_wash in car_wash_data:
        kb.button(
            text=f"🏢 {car_wash.name} (ID {car_wash.id})",
            callback_data=f"work_carwash_{car_wash.id}",
        )
    kb.button(text="🏠 Главное меню", callback_data=f"main_menu_{user_id}")
    kb.adjust(1)
    return kb.as_markup()


def admin_carwash_management_keyboard(
    car_wash_id: int,
    token: str,
    user_id: int = 2,
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    # Основные настройки
    kb.button(
        text="📝 Изменить описание", callback_data=f"edit_description_{car_wash_id}"
    )
    kb.button(text="🖼 Изменить фото", callback_data=f"edit_photo_{car_wash_id}")
    kb.button(
        text="⏰ Изменить время работы",
        callback_data=f"edit_working_hours_{car_wash_id}",
    )

    # Управление постами
    kb.button(
        text="🔧 Управлять постами",
        web_app=WebAppInfo(
            url=f"{settings.FRONT_URL}/posts/{car_wash_id}?token={token}"
        ),
    )

    # Статистика и брони
    kb.button(text="📊 Статистика", callback_data=f"carwash_stats_{car_wash_id}")
    kb.button(
        text="📋 Активные брони", callback_data=f"carwash_active_bookings_{car_wash_id}"
    )

    # Кнопка назад
    kb.button(text="⬅️ Назад", callback_data=f"manage_car_washes_{user_id}")

    # Располагаем кнопки в 2 колонки для лучшей читаемости
    kb.adjust(2, 2, 1, 2, 1)
    return kb.as_markup()
