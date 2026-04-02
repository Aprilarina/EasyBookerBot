from aiogram import F
from aiogram.dispatcher.router import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import WashPostID
from app.config import status_mapping
from app.dao.dao import BookingDAO, UserDAO, WashPostDAO
from app.tg_bot.create_bot import bot
from app.tg_bot.start.kbs import create_post_keyboard, main_keyboard
from app.tg_bot.start.schemas import UserCreate, UserIdModel


class BookingStates(StatesGroup):
    post_id = State()
    confirmed = State()


class PhoneStates(StatesGroup):
    phone = State()


router = Router()


@router.message(CommandStart())
async def send_phone_request(
    message: Message, session_with_commit: AsyncSession, state: FSMContext
):
    filters = UserIdModel(telegram_id=message.from_user.id)
    user_info = await UserDAO(session_with_commit).find_one_or_none(filters=filters)
    if user_info is None:
        phone_request_message = await message.answer(
            "Чтобы пользоваться ботом, поделитесь своим номером телефона. Для этого нажмите на кнопку ниже:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [
                        KeyboardButton(
                            text="Поделиться номером телефона", request_contact=True
                        )
                    ]
                ],
                resize_keyboard=True,
                one_time_keyboard=True,
            ),
        )
        await state.set_state(PhoneStates.phone)
        await state.update_data(
            phone_request_message_id=phone_request_message.message_id
        )
    else:
        await message.answer(
            f"Привет, {message.from_user.full_name}! Вас приветствует EasyBooker - сервис онлайн-бронирования автомоек в Одинцово! 🚗\n\nЗдесь вы сможете:\n• Забронировать мойку в удобное время\n• Выбрать подходящую услугу\n• Управлять своими бронями\n• Получать уведомления о статусе заказа\n\nДавайте начнем!",
            reply_markup=main_keyboard(user_info.id, user_info.owner),
        )


@router.message(PhoneStates.phone)
async def process_phone(
    message: Message, state: FSMContext, session_with_commit: AsyncSession
):
    user_data = UserCreate(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        firstname=message.from_user.first_name,
        lastname=message.from_user.last_name,
        phone=message.contact.phone_number,
    )
    user_new = await UserDAO(session_with_commit).add(user_data)

    # Получаем ID сообщения с запросом телефона
    state_data = await state.get_data()
    phone_request_message_id = state_data.get("phone_request_message_id")

    # Удаляем сообщение с запросом телефона
    if phone_request_message_id:
        try:
            await bot.delete_message(message.chat.id, phone_request_message_id)
        except Exception:
            pass

    # Удаляем сообщение с контактом пользователя
    try:
        await bot.delete_message(message.chat.id, message.message_id)
    except Exception:
        pass

    await state.clear()
    # Отправляем только приветственное сообщение с основной клавиатурой
    await message.answer(
        f"Привет, {message.from_user.full_name}! Вас приветствует EasyBooker - сервис онлайн-бронирования автомоек в Одинцово! 🚗\n\nЗдесь вы сможете:\n• Забронировать мойку в удобное время\n• Выбрать подходящую услугу\n• Управлять своими бронями\n• Получать уведомления о статусе заказа\n\nДавайте начнем!",
        reply_markup=main_keyboard(user_new.id, user_new.owner),
    )


@router.callback_query(F.data.startswith("reject_order_"))
async def reject_order(
    call: CallbackQuery, state: FSMContext, session_with_commit: AsyncSession
):
    await state.clear()
    try:
        await call.answer("Отклоняю бронь!")
    except Exception:
        pass
    order_id, user_id = call.data.replace("reject_order_", "").split("_")
    order_info = await BookingDAO(session_with_commit).find_one_or_none_by_id(
        int(order_id)
    )
    user_info = await UserDAO(session_with_commit).find_one_or_none_by_id(int(user_id))

    if not user_info:
        await call.message.answer(f"❌ Ошибка: пользователь c ID {user_id} не найден!")
        return

    user_info_tg_id = user_info.telegram_id
    if not order_info:
        await call.message.answer(
            "❌ Бронь не найдена!",
            reply_markup=main_keyboard(user_info.id, user_info.owner),
        )
        return

    booking_info = await BookingDAO(session_with_commit).get_booking_full_info(
        int(order_id)
    )

    if not booking_info:
        await call.message.answer("❌ Ошибка: информация о брони не найдена!")
        return

    order_info.status = "admin_rejected"

    # Сообщение для администратора
    admin_text = f"""
✅ <b>Бронь #{booking_info['id']} успешно отклонена!</b>

🚗 Автомобиль: {booking_info['user_auto']['brand']['name']} {booking_info['user_auto']['model']['name']} ({booking_info['user_auto']['car_number']})
👤 Клиент: {booking_info['user']['firstname']} {booking_info['user']['lastname']}
🧼 Услуга: {booking_info['service']['name']}
📅 Дата: {booking_info['booking_date']}
🕒 Время: {booking_info['booking_time']}
"""

    # Сообщение для клиента
    client_text = f"""
❌ <b>Ваша бронь #{booking_info['id']} была отклонена!</b>

🏢 Автомойка: {booking_info['car_wash']['name']}
🧼 Услуга: {booking_info['service']['name']}
💰 Стоимость: {booking_info['service']['price']} руб.
📅 Дата: {booking_info['booking_date']}
🕒 Время: {booking_info['booking_time']}

Приносим извинения за неудобства. Пожалуйста, выберите другое время или свяжитесь с нами для уточнения деталей.
"""

    # Удаляем сообщение с информацией о брони
    try:
        await call.message.delete()
    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")

    await call.message.answer(
        admin_text,
        parse_mode="HTML",
        reply_markup=main_keyboard(user_info.id, user_info.owner),
    )
    await bot.send_message(
        int(user_info_tg_id),
        client_text,
        parse_mode="HTML",
        reply_markup=main_keyboard(user_info.id, user_info.owner),
    )


@router.callback_query(F.data.startswith("accept_order_"))
async def accept_order(
    call: CallbackQuery, state: FSMContext, session_with_commit: AsyncSession
):
    await state.clear()
    await call.answer("Принимаю бронь!")
    order_id, user_id = call.data.replace("accept_order_", "").split("_")
    try:
        await call.message.delete()
    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")
    booking_info = await BookingDAO(session_with_commit).get_booking_full_info(
        int(order_id)
    )

    wash_posts = await WashPostDAO(session_with_commit).find_all(
        WashPostID(car_wash_id=booking_info.get("car_wash").get("id"), is_open=True)
    )
    kb = create_post_keyboard(wash_posts)
    await state.update_data(
        order_id=int(order_id), user_id=int(user_id), booking_info=booking_info
    )

    # Удаляем сообщение с информацией о брони
    try:
        await call.message.delete()
    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")

    await call.message.answer(
        f"На данный момент свободных постов {len(wash_posts)}шт. Выберите номер поста",
        reply_markup=kb,
    )
    await state.set_state(BookingStates.post_id)


@router.callback_query(F.data.startswith("post_"))
async def post_selected(
    call: CallbackQuery, state: FSMContext, session_with_commit: AsyncSession
):
    await state.update_data(post_id=int(call.data.replace("post_", "")))
    data = await state.get_data()
    booking_info = data.get("booking_info")
    post_id = data.get("post_id")

    # Получаем информацию о посте
    post_info = await WashPostDAO(session_with_commit).find_one_or_none_by_id(post_id)
    post_number = post_info.post_number if post_info else "Неизвестный"

    confirmation_text = f"""
⚠️ <b>Вы уверены, что хотите подтвердить бронь?</b>

🚗 Автомобиль: {booking_info['user_auto']['brand']['name']} {booking_info['user_auto']['model']['name']} ({booking_info['user_auto']['car_number']})
👤 Клиент: {booking_info['user']['firstname']} {booking_info['user']['lastname']}
🏢 Автомойка: {booking_info['car_wash']['name']}
🧼 Услуга: {booking_info['service']['name']}
💰 Стоимость: {booking_info['service']['price']} руб.
📅 Дата: {booking_info['booking_date']}
🕒 Время: {booking_info['booking_time']}
🚿 Пост №{post_number} (ID {post_id})

Пожалуйста, подтвердите ваш выбор.
"""

    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Подтвердить", callback_data=f"confirm_post_{post_id}")
    kb.button(text="❌ Отменить", callback_data="cancel_post_selection")
    kb.adjust(1)

    await call.message.answer(
        confirmation_text, parse_mode="HTML", reply_markup=kb.as_markup()
    )
    await state.set_state(BookingStates.confirmed)


@router.callback_query(F.data.startswith("confirm_post_"))
async def confirm_post(
    call: CallbackQuery, state: FSMContext, session_with_commit: AsyncSession
):
    try:
        await call.message.delete()
    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")
    data = await state.get_data()
    booking_info = data.get("booking_info")
    post_id = data.get("post_id")
    order_id = data.get("order_id")

    order_info = await BookingDAO(session_with_commit).find_one_or_none_by_id(
        int(order_id)
    )

    post_info = await WashPostDAO(session_with_commit).find_one_or_none_by_id(post_id)
    post_info.is_open = False
    # Обновляем статус брони
    if order_info:
        order_info.status = "confirmed"
        order_info.post_id = post_id

        # Формируем сообщение для клиента
        client_message = f"""
🎉 <b>Ваша бронь подтверждена!</b>

🚗 Автомобиль: {booking_info['user_auto']['brand']['name']} {booking_info['user_auto']['model']['name']} ({booking_info['user_auto']['car_number']})
🏢 Автомойка: {booking_info['car_wash']['name']}
🧼 Услуга: {booking_info['service']['name']}
💰 Стоимость: {booking_info['service']['price']} руб.
📅 Дата: {booking_info['booking_date']}
🕒 Время: {booking_info['booking_time']}
🚿 Пост №{post_info.post_number}

⚠️ <b>Важно:</b> Мы ждем вас в течение 30 минут с момента подтверждения брони. 
В случае опоздания ваше место может быть отдано другому клиенту.

Спасибо, что выбрали нас! Ждем вас!
"""

        # Создаем клавиатуру для клиента
        client_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📍 Как добраться",
                        url=f"https://yandex.ru/maps/?text={booking_info['car_wash']['address']}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ Отменить",
                        callback_data=f"cancel_booking_{order_id}",
                    )
                ],
            ]
        )

        # Отправляем сообщение клиенту
        await call.bot.send_message(
            chat_id=booking_info["user"]["telegram_id"],
            text=client_message,
            parse_mode="HTML",
            reply_markup=client_keyboard,
        )

        await call.answer("Бронь подтверждена!")
        user_info = await UserDAO(session_with_commit).get_user_info_by_telegram_id(
            int(call.from_user.id)
        )
        await call.message.answer(
            "Клиент уведомлен о подтверждении брони.",
            reply_markup=main_keyboard(user_info.id, user_info.owner),
        )
    else:
        await call.answer("Ошибка: бронь не найдена", show_alert=True)

    await state.clear()


@router.callback_query(F.data == "about_us")
async def about_us(call: CallbackQuery, session_with_commit: AsyncSession):
    user_info = await UserDAO(session_with_commit).get_user_info_by_telegram_id(
        int(call.from_user.id)
    )
    about_text = """
🚗 <b>О нас</b> 🚿

Мы - сервис онлайн-бронирования автомоек в городе Одинцово!

✅ <b>Что мы предлагаем:</b>
• Удобное бронирование автомойки в несколько кликов
• Выбор подходящего времени без звонков и ожиданий
• Полный список доступных услуг и цен
• Уведомления о статусе вашего заказа

🏢 <b>Наши автомойки:</b>
Мы сотрудничаем с лучшими автомойками Одинцово, чтобы предоставить вам качественный сервис.

⏱ <b>Экономьте время:</b>
Забудьте о долгих ожиданиях в очереди - бронируйте заранее и приезжайте к назначенному времени!

Спасибо, что выбрали наш сервис! Мы стремимся сделать процесс мойки вашего автомобиля максимально удобным и приятным.
"""
    await call.message.edit_text(
        about_text,
        parse_mode="HTML",
        reply_markup=main_keyboard(user_info.id, user_info.owner),
    )
    await call.answer()


@router.callback_query(F.data.startswith("my_bookings_"))
async def my_bookings(call: CallbackQuery, session_without_commit: AsyncSession):
    telegram_id = call.from_user.id
    user = await UserDAO(session_without_commit).get_user_info_by_telegram_id(
        telegram_id
    )

    if not user:
        await call.answer("Ошибка: пользователь не найден")
        return

    bookings = await BookingDAO(session_without_commit).get_user_bookings_full_info(
        user.id
    )

    if not bookings or len(bookings) == 0:
        kb = InlineKeyboardBuilder()
        kb.button(text="⬅️ Назад", callback_data=f"main_menu_{user.id}")
        kb.adjust(1)
        await call.message.edit_text(
            "У вас пока нет броней.", reply_markup=kb.as_markup()
        )
        await call.answer()
        return

    # Подсчитываем статистику
    total_bookings = len(bookings)
    status_counts = {}
    active_bookings = []

    for booking in bookings:
        status = booking["status"]
        status_counts[status] = status_counts.get(status, 0) + 1
        if status in ["pending", "confirmed"]:
            active_bookings.append(booking)

    # Формируем текст статистики
    stats_text = f"""
📊 <b>Статистика ваших броней:</b>

Всего броней: {total_bookings}
Активных броней: {len(active_bookings)}

Статусы:
✅ Подтверждено: {status_counts.get('confirmed', 0)}
⏳ Ожидает: {status_counts.get('pending', 0)}
❌ Отменено: {status_counts.get('user_rejected', 0) + status_counts.get('admin_rejected', 0)}
✅ Завершено: {status_counts.get('completed', 0)}
"""

    # Создаем клавиатуру для статистики
    kb = InlineKeyboardBuilder()
    if active_bookings:
        kb.button(
            text="🚗 Управлять активными бронями",
            callback_data=f"manage_active_bookings_{user.id}",
        )
    kb.button(text="⬅️ Назад", callback_data=f"main_menu_{user.id}")
    kb.adjust(1)

    # Отправляем статистику
    await call.message.edit_text(
        stats_text, parse_mode="HTML", reply_markup=kb.as_markup()
    )
    await call.answer()


@router.callback_query(F.data.startswith("manage_active_bookings_"))
async def show_active_bookings(call: CallbackQuery, session_with_commit: AsyncSession):
    user_id = int(call.data.replace("manage_active_bookings_", ""))
    bookings = await BookingDAO(session_with_commit).get_user_bookings_full_info(
        user_id
    )
    status_counts = {}
    active_bookings = []

    for booking in bookings:
        status = booking["status"]
        status_counts[status] = status_counts.get(status, 0) + 1
        if status in ["pending", "confirmed"]:
            active_bookings.append(booking)

    if not len(active_bookings) > 0:
        kb = InlineKeyboardBuilder()
        kb.button(text="⬅️ Назад", callback_data=f"my_bookings_{user_id}")
        kb.adjust(1)
        await call.message.edit_text(
            "У вас нет активных броней.", reply_markup=kb.as_markup()
        )
        await call.answer()
        return

    # Удаляем предыдущее сообщение со списком броней
    try:
        await call.message.delete()
    except Exception:
        pass

    for booking in active_bookings:
        text = (
            f"🚗 Бронь #{booking['id']}\n\n"
            f"📍 Автомойка: {booking['car_wash']['name']}\n"
            f"📝 Услуга: {booking['service']['name']}\n"
            f"💰 Цена: {booking['service']['price']}₽\n"
            f"📅 Дата: {booking['booking_date']}\n"
            f"🕒 Время: {booking['booking_time']}\n"
            f"🚘 Авто: {booking['user_auto']['brand']['name']} {booking['user_auto']['model']['name']}\n"
            f"📋 Номер: {booking['user_auto']['car_number']}\n"
            f"📍 Пост: {booking['post']['post_number'] if booking['post'] else 'Не назначен'}\n"
            f"📊 Статус: {status_mapping.get(booking['status'], booking['status'])}"
        )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="❌ Отменить",
                        callback_data=f"cancel_booking_{booking['id']}",
                    )
                ]
            ]
        )

        if booking["status"] == "confirmed":
            keyboard.inline_keyboard.append(
                [
                    InlineKeyboardButton(
                        text="📍 Как добраться",
                        url=f"https://yandex.ru/maps/?text={booking['car_wash']['address']}",
                    )
                ]
            )

        await call.message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("cancel_booking_"))
async def cancel_booking(call: CallbackQuery, session_with_commit: AsyncSession):
    booking_id = int(call.data.replace("cancel_booking_", ""))
    booking = await BookingDAO(session_with_commit).find_one_or_none_by_id(booking_id)
    if not booking:
        await call.answer("Бронь не найдена!")
        return

    booking_info = await BookingDAO(session_with_commit).get_booking_full_info(
        booking_id
    )
    booking.status = "user_rejected"

    if booking.post_id:
        post_info = await WashPostDAO(session_with_commit).find_one_or_none_by_id(
            booking.post_id
        )
        if post_info:
            post_info.is_open = True

    if booking_info:
        admin_id = int(booking_info["car_wash"]["admin_id"])
        car_info = (
            f"{booking_info['user_auto']['brand']['name']} {booking_info['user_auto']['model']['name']}"
            if booking_info.get("user_auto")
            else "Не указано"
        )
        car_number = (
            booking_info["user_auto"]["car_number"]
            if booking_info.get("user_auto")
            else "Не указано"
        )

        notification_text = (
            f"❌ Отмена брони #{booking_id}\n\n"
            f"🚘 Авто: {car_info}\n"
            f"📋 Номер: {car_number}\n"
            f"📅 Дата: {booking_info.get('booking_date', 'Не указана')}\n"
            f"🕒 Время: {booking_info.get('booking_time', 'Не указано')}"
        )
        admin_info = await UserDAO(session_with_commit).find_one_or_none_by_id(admin_id)
        try:
            await bot.send_message(
                chat_id=admin_info.telegram_id, text=notification_text
            )
        except Exception:
            pass

    # Удаляем сообщение с информацией о брони
    await call.message.delete()
    await call.answer("Бронь отменена!")
