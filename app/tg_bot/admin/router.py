import os
from datetime import datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings, status_mapping
from app.dao.dao import BookingDAO, CarWashDAO, UserDAO, WashPostDAO
from app.tg_bot.admin.kbs import admin_carwash_management_keyboard, admin_main_keyboard
from app.tg_bot.admin.schemas import WashOwnerID
from app.tg_bot.create_bot import bot
from app.tg_bot.start.kbs import main_keyboard

router = Router()


@router.callback_query(F.data.startswith("manage_car_washes_"))
async def start_admin_washes(
    call: CallbackQuery, state: FSMContext, session_with_commit: AsyncSession
):
    await state.clear()
    # Проверка на None перед использованием метода replace
    if call.data is None:
        return

    user_id = int(call.data.replace("manage_car_washes_", ""))
    my_washes = await CarWashDAO(session_with_commit).find_all(
        WashOwnerID(owner_id=user_id)
    )

    # Преобразуем my_washes в формат, ожидаемый функцией admin_main_keyboard
    kb = admin_main_keyboard(list(my_washes), user_id)

    # Проверка на None перед использованием метода edit_text
    if call.message is None:
        return

    # Используем безопасный метод для редактирования сообщения
    try:
        await call.message.edit_text("Выберите автомойку для работы", reply_markup=kb)
    except Exception:
        # Обработка ошибки, если сообщение недоступно для редактирования
        pass


@router.callback_query(F.data.startswith("work_carwash_"))
async def work_carwash(
    call: CallbackQuery, state: FSMContext, session_with_commit: AsyncSession
):
    await state.clear()
    car_wash_id = int(call.data.replace("work_carwash_", ""))
    car_wash = await CarWashDAO(session_with_commit).find_one_or_none_by_id(car_wash_id)
    if car_wash is None:
        return
    kb = admin_carwash_management_keyboard(car_wash_id, car_wash.token)
    await call.message.edit_text("Выберите действие", reply_markup=kb)
    await call.answer()


class PhotoUploadStates(StatesGroup):
    waiting_for_photo = State()


class DescriptionEditStates(StatesGroup):
    waiting_for_description = State()


class WorkingHoursStates(StatesGroup):
    waiting_for_start_time = State()
    waiting_for_end_time = State()
    waiting_for_work_days = State()


@router.callback_query(F.data.startswith("edit_photo_"))
async def edit_photo_start(call: CallbackQuery, state: FSMContext):
    car_wash_id = int(call.data.replace("edit_photo_", ""))
    await state.update_data(car_wash_id=car_wash_id)
    await state.set_state(PhotoUploadStates.waiting_for_photo)
    await call.message.answer("Пожалуйста, отправьте новую фотографию для автомойки.")
    await call.answer()


@router.message(PhotoUploadStates.waiting_for_photo, F.photo | F.document)
async def process_photo_upload(
    message: Message, state: FSMContext, session_with_commit: AsyncSession
):
    data = await state.get_data()
    car_wash_id = data.get("car_wash_id")

    # Получаем информацию об автомойке
    car_wash = await CarWashDAO(session_with_commit).find_one_or_none_by_id(car_wash_id)
    token = car_wash.token
    if car_wash is None:
        await message.answer("Ошибка: автомойка не найдена.")
        await state.clear()
        return

    # Создаем директорию, если она не существует

    os.makedirs(settings.STATIC_DIR, exist_ok=True)

    # Генерируем имя файла

    file_name = f"carwash_{car_wash_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
    file_path = os.path.join(settings.STATIC_DIR, file_name)

    # Скачиваем и сохраняем фото
    try:
        if message.photo:
            # Берем фото с наилучшим качеством (последнее в списке)
            file_id = message.photo[-1].file_id
        else:  # документ
            file_id = message.document.file_id

        file = await message.bot.get_file(file_id)
        await message.bot.download_file(file.file_path, file_path)

        # Обновляем путь к фото в базе данных
        car_wash.photo_url = f"/static/{file_name}"
        await message.answer(
            f"Фотография для автомойки '{car_wash.name}' успешно обновлена!"
        )

        # Показываем клавиатуру управления автомойкой
        kb = admin_carwash_management_keyboard(car_wash_id, token)
        await message.answer("Выберите дальнейшее действие:", reply_markup=kb)

    except Exception as e:
        await message.answer(f"Произошла ошибка при сохранении фотографии: {str(e)}")

    await state.clear()


@router.callback_query(F.data.startswith("edit_description_"))
async def edit_description_start(call: CallbackQuery, state: FSMContext):
    car_wash_id = int(call.data.replace("edit_description_", ""))
    await state.update_data(car_wash_id=car_wash_id)
    await state.set_state(DescriptionEditStates.waiting_for_description)
    await call.message.answer("Пожалуйста, отправьте новое описание для автомойки.")
    await call.answer()


@router.message(DescriptionEditStates.waiting_for_description)
async def process_description_edit(
    message: Message, state: FSMContext, session_with_commit: AsyncSession
):
    data = await state.get_data()
    car_wash_id = data.get("car_wash_id")
    new_description = message.text

    # Получаем информацию об автомойке
    car_wash = await CarWashDAO(session_with_commit).find_one_or_none_by_id(car_wash_id)
    if car_wash is None:
        await message.answer("Ошибка: автомойка не найдена.")
        await state.clear()
        return

    # Обновляем описание в базе данных
    car_wash.description = new_description
    await message.answer(f"Описание для автомойки '{car_wash.name}' успешно обновлено!")

    # Показываем клавиатуру управления автомойкой
    kb = admin_carwash_management_keyboard(car_wash_id, car_wash.token)
    await message.answer("Выберите дальнейшее действие:", reply_markup=kb)

    await state.clear()


@router.callback_query(F.data.startswith("edit_working_hours_"))
async def edit_working_hours_start(call: CallbackQuery, state: FSMContext):
    car_wash_id = int(call.data.replace("edit_working_hours_", ""))
    await state.update_data(car_wash_id=car_wash_id)
    await state.set_state(WorkingHoursStates.waiting_for_start_time)
    await call.message.answer(
        "Пожалуйста, введите время начала работы в формате ЧЧ:ММ (например, 09:00)"
    )
    await call.answer()


@router.message(WorkingHoursStates.waiting_for_start_time)
async def process_start_time(message: Message, state: FSMContext):
    # Проверяем формат времени
    try:
        hours, minutes = map(int, message.text.split(":"))
        if not (0 <= hours <= 23 and 0 <= minutes <= 59):
            raise ValueError
    except ValueError:
        await message.answer(
            "Неверный формат времени. Пожалуйста, введите время в формате ЧЧ:ММ (например, 09:00)"
        )
        return

    await state.update_data(work_start=message.text)
    await state.set_state(WorkingHoursStates.waiting_for_end_time)
    await message.answer(
        "Теперь введите время окончания работы в формате ЧЧ:ММ (например, 21:00)"
    )


@router.message(WorkingHoursStates.waiting_for_end_time)
async def process_end_time(message: Message, state: FSMContext):
    # Проверяем формат времени
    try:
        hours, minutes = map(int, message.text.split(":"))
        if not (0 <= hours <= 23 and 0 <= minutes <= 59):
            raise ValueError
    except ValueError:
        await message.answer(
            "Неверный формат времени. Пожалуйста, введите время в формате ЧЧ:ММ (например, 21:00)"
        )
        return

    await state.update_data(work_end=message.text)
    await state.set_state(WorkingHoursStates.waiting_for_work_days)
    await message.answer(
        "Введите рабочие дни через запятую (например: пн,вт,ср,чт,пт,сб,вс)"
    )


@router.message(WorkingHoursStates.waiting_for_work_days)
async def process_work_days(
    message: Message, state: FSMContext, session_with_commit: AsyncSession
):
    data = await state.get_data()
    car_wash_id = data.get("car_wash_id")
    work_start = data.get("work_start")
    work_end = data.get("work_end")
    work_days = message.text.lower().strip()

    # Получаем информацию об автомойке
    car_wash = await CarWashDAO(session_with_commit).find_one_or_none_by_id(car_wash_id)
    if car_wash is None:
        await message.answer("Ошибка: автомойка не найдена.")
        await state.clear()
        return

    # Обновляем время работы в базе данных
    car_wash.work_start = work_start
    car_wash.work_end = work_end
    car_wash.work_days = work_days

    await message.answer(
        f"Время работы для автомойки '{car_wash.name}' успешно обновлено!"
    )

    # Показываем клавиатуру управления автомойкой
    kb = admin_carwash_management_keyboard(car_wash_id, car_wash.token)
    await message.answer("Выберите дальнейшее действие:", reply_markup=kb)

    await state.clear()


@router.callback_query(F.data.startswith("carwash_stats_"))
async def show_carwash_statistics(
    call: CallbackQuery, session_with_commit: AsyncSession
):
    car_wash_id = int(call.data.replace("carwash_stats_", ""))
    stats = await BookingDAO(session_with_commit).get_carwash_statistics(car_wash_id)

    if not stats:
        kb = InlineKeyboardBuilder()
        kb.button(text="⬅️ Назад", callback_data=f"work_carwash_{car_wash_id}")
        kb.adjust(1)
        await call.message.edit_text(
            "Для этой автомойки пока нет статистики.", reply_markup=kb.as_markup()
        )
        await call.answer()
        return

    status_text = "\n".join(
        [
            f"• {status_mapping.get(status, status)}: {count}"
            for status, count in stats["status_counts"].items()
        ]
    )

    message = f"""
📊 <b>Статистика автомойки</b>

📈 Всего броней: {stats['total_bookings']}
💰 Общая выручка: {stats['total_revenue']}₽

📋 Распределение по статусам:
{status_text}
"""

    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ Назад", callback_data=f"work_carwash_{car_wash_id}")
    kb.adjust(1)

    await call.message.edit_text(
        message, parse_mode="HTML", reply_markup=kb.as_markup()
    )
    await call.answer()


@router.callback_query(F.data.startswith("carwash_active_bookings_"))
async def show_carwash_active_bookings(
    call: CallbackQuery, session_without_commit: AsyncSession
):
    try:
        car_wash_id = int(call.data.replace("carwash_active_bookings_", ""))
        active_bookings = await BookingDAO(
            session_without_commit
        ).get_carwash_active_bookings(car_wash_id)

        if not active_bookings:
            kb = InlineKeyboardBuilder()
            kb.button(text="⬅️ Назад", callback_data=f"work_carwash_{car_wash_id}")
            kb.adjust(1)
            await call.message.edit_text(
                "У автомойки нет активных броней.", reply_markup=kb.as_markup()
            )
            await call.answer()
            return

        # Удаляем предыдущее сообщение
        try:
            await call.message.delete()
        except Exception as e:
            logger.error(f"Ошибка при удалении сообщения: {e}")

        for booking in active_bookings:
            try:
                text = (
                    f"🚗 Бронь #{booking['id']}\n\n"
                    f"👤 Клиент: {booking['user']['firstname']} {booking['user']['lastname']}\n"
                    f"📝 Услуга: {booking['service']['name']}\n"
                    f"💰 Цена: {booking['service']['price']}₽\n"
                    f"📅 Дата: {booking['booking_date']}\n"
                    f"🕒 Время: {booking['booking_time']}\n"
                    f"🚘 Авто: {booking['user_auto']['brand']['name']} {booking['user_auto']['model']['name']}\n"
                    f"📋 Номер: {booking['user_auto']['car_number']}\n"
                    f"📍 Пост: {booking['post']['post_number'] if booking['post'] else 'Не назначен'}\n"
                    f"📊 Статус: {status_mapping.get(booking['status'], booking['status'])}"
                )

                kb = InlineKeyboardBuilder()
                print(booking)
                if booking["status"] == "pending":
                    kb.button(
                        text="✅ Принять",
                        callback_data=f"accept_order_{booking['id']}_{booking['user']['id']}",
                    )
                    kb.button(
                        text="❌ Отклонить",
                        callback_data=f"reject_order_{booking['id']}_{booking['user']['id']}",
                    )
                elif booking["status"] == "confirmed":
                    kb.button(
                        text="❌ Отменить",
                        callback_data=f"cancel_bookinga_{booking['id']}",
                    )
                    kb.button(
                        text="✅ Завершить",
                        callback_data=f"complete_booking_{booking['id']}",
                    )

                kb.button(text="⬅️ Назад", callback_data=f"work_carwash_{car_wash_id}")
                kb.adjust(2, 1)

                await call.message.answer(text, reply_markup=kb.as_markup())
            except Exception as e:
                logger.error(
                    f"Ошибка при обработке брони {booking.get('id', 'unknown')}: {e}"
                )
                continue

    except Exception as e:
        logger.error(f"Ошибка при получении активных броней: {e}")
        await call.message.edit_text(
            "Произошла ошибка при получении данных. Пожалуйста, попробуйте позже."
        )
        await call.answer()


@router.callback_query(F.data.startswith("complete_booking_"))
async def complete_booking(call: CallbackQuery, session_with_commit: AsyncSession):
    try:
        if not call.message:
            await call.answer("Ошибка: сообщение недоступно")
            return

        booking_id = int(call.data.replace("complete_booking_", ""))
        booking = await BookingDAO(session_with_commit).find_one_or_none_by_id(
            booking_id
        )

        if not booking:
            await call.answer("Бронь не найдена!")
            return

        booking_info = await BookingDAO(session_with_commit).get_booking_full_info(
            booking_id
        )
        if not booking_info:
            await call.answer("Ошибка при получении информации о брони!")
            return

        booking.status = "completed"

        if booking.post_id:
            post_info = await WashPostDAO(session_with_commit).find_one_or_none_by_id(
                booking.post_id
            )
            if post_info:
                post_info.is_open = True

        # Формируем сообщение для пользователя
        user_message = f"""
🎉 <b>Спасибо за посещение!</b>

Мы надеемся, что вы остались довольны качеством обслуживания в автомойке <b>{booking_info['car_wash']['name']}</b>.

Пожалуйста, поделитесь вашим отзывом о нашей работе.
"""

        # Создаем клавиатуру с кнопкой отзыва
        review_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✍️ Оставить отзыв",
                        web_app=WebAppInfo(
                            url=f"{settings.FRONT_URL}/wash_info/{booking_info['car_wash']['id']}?user_id={booking_info['user']['id']}"
                        ),
                    )
                ]
            ]
        )

        # Отправляем сообщение пользователю
        try:
            await bot.send_message(
                chat_id=booking_info["user"]["telegram_id"],
                text=user_message,
                parse_mode="HTML",
                reply_markup=review_keyboard,
            )
        except Exception as e:
            print(f"Ошибка при отправке сообщения пользователю: {e}")

        # Удаляем сообщение с информацией о брони
        try:
            await call.message.delete()
        except Exception as e:
            print(f"Ошибка при удалении сообщения: {e}")

        await call.answer("Бронь завершена!")
    except Exception as e:
        print(f"Ошибка при завершении брони: {e}")
        await call.answer("Произошла ошибка при завершении брони!")


@router.callback_query(F.data.startswith("cancel_bookinga_"))
async def cancel_booking(call: CallbackQuery, session_with_commit: AsyncSession):
    try:
        if not call.message:
            await call.answer("Ошибка: сообщение недоступно")
            return

        booking_id = int(call.data.replace("cancel_booking_", ""))
        booking = await BookingDAO(session_with_commit).find_one_or_none_by_id(
            booking_id
        )

        if not booking:
            await call.answer("Бронь не найдена!")
            return

        booking_info = await BookingDAO(session_with_commit).get_booking_full_info(
            booking_id
        )
        if not booking_info:
            await call.answer("Ошибка при получении информации о брони!")
            return

        booking.status = "admin_rejected"

        if booking.post_id:
            post_info = await WashPostDAO(session_with_commit).find_one_or_none_by_id(
                booking.post_id
            )
            if post_info:
                post_info.is_open = True

        # Формируем сообщение для пользователя
        user_message = f"""
❌ <b>Ваша бронь #{booking_info['id']} была отменена администратором</b>

🏢 Автомойка: {booking_info['car_wash']['name']}
🧼 Услуга: {booking_info['service']['name']}
💰 Стоимость: {booking_info['service']['price']} руб.
📅 Дата: {booking_info['booking_date']}
🕒 Время: {booking_info['booking_time']}
🚘 Авто: {booking_info['user_auto']['brand']['name']} {booking_info['user_auto']['model']['name']}
📋 Номер: {booking_info['user_auto']['car_number']}

Приносим извинения за неудобства. Пожалуйста, выберите другое время или свяжитесь с нами для уточнения деталей.
"""

        # Создаем клавиатуру для пользователя
        user_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📞 Связаться с нами",
                        url=f"https://t.me/{booking_info['car_wash']['admin_id']}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🚗 Записаться снова",
                        callback_data=f"my_bookings_{booking_info['user']['id']}",
                    )
                ],
            ]
        )

        # Отправляем сообщение пользователю
        try:
            await bot.send_message(
                chat_id=booking_info["user"]["telegram_id"],
                text=user_message,
                parse_mode="HTML",
                reply_markup=user_keyboard,
            )
        except Exception as e:
            print(f"Ошибка при отправке сообщения пользователю: {e}")

        # Удаляем сообщение с информацией о брони
        try:
            await call.message.delete()
        except Exception as e:
            print(f"Ошибка при удалении сообщения: {e}")

        await call.answer("Бронь отменена!")
    except Exception as e:
        print(f"Ошибка при отмене брони: {e}")
        await call.answer("Произошла ошибка при отмене брони!")


@router.callback_query(F.data.startswith("main_menu_"))
async def return_to_main_menu(call: CallbackQuery, session_with_commit: AsyncSession):
    user_id = int(call.data.replace("main_menu_", ""))
    user_info = await UserDAO(session_with_commit).find_one_or_none_by_id(user_id)

    if not user_info:
        await call.answer("Ошибка: пользователь не найден!")
        return

    await call.message.edit_text(
        "🏠 <b>Главное меню</b>\n\nВыберите действие:",
        parse_mode="HTML",
        reply_markup=main_keyboard(user_info.id, user_info.owner),
    )
    await call.answer()
