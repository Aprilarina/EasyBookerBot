from aiogram.types import InlineKeyboardMarkup, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.config import settings


def main_keyboard(user_id: int, owner: bool = False) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text="🚗 Записаться", web_app=WebAppInfo(url=f"{settings.FRONT_URL}/{user_id}")
    )
    kb.button(text="📋 Мои брони", callback_data=f"my_bookings_{user_id}")
    kb.button(text="ℹ️ О нас", callback_data="about_us")
    if owner:
        kb.button(text="🏢 Мои автомойки", callback_data=f"manage_car_washes_{user_id}")
    kb.adjust(1)
    return kb.as_markup()


def order_rule_keyboard(order, user_id) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text="❌ Отклонить заказ", callback_data=f"reject_order_{order.id}_{user_id}"
    )
    kb.button(
        text="✅ Принять заказ", callback_data=f"accept_order_{order.id}_{user_id}"
    )
    kb.adjust(1)
    return kb.as_markup()


def create_post_keyboard(wash_posts) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for post in wash_posts:
        kb.button(text=f"🔧 №{post.post_number}", callback_data=f"post_{post.id}")
    kb.adjust(2)  # Располагаем кнопки в 2 колонки
    return kb.as_markup()
