from fastapi import APIRouter, BackgroundTasks, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.api.schemas import (
    CarWashID,
    ModelMarkID,
    ReviewID,
    SCar,
    SOrder,
    SReview,
    SWatchPostId,
    UserAutosID,
    WashPostID,
)
from app.dao.dao import (
    BookingDAO,
    BrandDAO,
    CarWashDAO,
    CarWashServiceDAO,
    ModelDAO,
    ReviewDAO,
    ServiceDAO,
    UserDAO,
    UsersAutosDAO,
    WashPostDAO,
)
from app.dao.database import async_session_maker
from app.dao.fast_api_dep import get_session_with_commit, get_session_without_commit
from app.dao.models import Review
from app.tg_bot.create_bot import bot
from app.tg_bot.start.kbs import order_rule_keyboard

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/user_info/{user_id}")
async def user_info(
    user_id: int, session: AsyncSession = Depends(get_session_without_commit)
):
    return await UserDAO(session).find_one_or_none_by_id(user_id)


@router.get("/all_brands")
async def all_brands(session: AsyncSession = Depends(get_session_without_commit)):
    return await BrandDAO(session).find_all()


@router.get("/car_models/{mark_id}")
async def all_models(
    mark_id: str, session: AsyncSession = Depends(get_session_without_commit)
):
    return await ModelDAO(session).find_all(ModelMarkID(mark_id=mark_id))


@router.get("/user_cars/{user_id}")
async def user_autos(
    user_id: int, session: AsyncSession = Depends(get_session_without_commit)
):
    return await UsersAutosDAO(session).find_all(UserAutosID(user_id=user_id))


@router.get("/car_wash_list")
async def car_wash_list(session: AsyncSession = Depends(get_session_with_commit)):
    all_wash = await CarWashDAO(session).find_all()
    for wash in all_wash:
        wash_posts = await WashPostDAO(session).find_all(
            WashPostID(car_wash_id=wash.id, is_open=True)
        )
        if wash_posts:
            wash.busy = False
        else:
            wash.busy = True
    return all_wash


@router.get("/carwash_info/{car_wash_id}")
async def car_wash_info(
    car_wash_id: int, session: AsyncSession = Depends(get_session_with_commit)
):
    car_wash = await CarWashDAO(session).find_one_or_none_by_id(car_wash_id)
    if car_wash:
        wash_posts = await WashPostDAO(session).find_all(
            WashPostID(car_wash_id=car_wash_id, is_open=True)
        )
        if wash_posts:
            car_wash.busy = False
        else:
            car_wash.busy = True
    return car_wash


@router.get("/carwash_services/{car_wash_id}")
async def car_wash_services(
    car_wash_id: int, session: AsyncSession = Depends(get_session_without_commit)
):
    all_data = await CarWashServiceDAO(session).find_all_with_service(
        CarWashID(car_wash_id=car_wash_id)
    )
    return all_data


@router.post("/create_order_start")
async def create_order_start(
    order: SOrder,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session_with_commit),
):
    # Добавляем заказ в базу данных
    created_order = await BookingDAO(session).add(order)

    # Запускаем фоновую задачу для отправки уведомления
    background_tasks.add_task(send_order_notification, order_id=created_order.id)

    return {"message": "Заказ успешно создан", "order_id": created_order.id}


async def send_order_notification(order_id: int):
    async with async_session_maker() as session:
        order = await BookingDAO(session).find_one_or_none_by_id(order_id)
        if not order:
            return

        user_auto = await UsersAutosDAO(session).find_one_or_none_by_id(
            order.user_auto_id
        )
        user_info = await UserDAO(session).find_one_or_none_by_id(order.user_id)
        car_wash = await CarWashDAO(session).find_one_or_none_by_id(order.car_wash_id)
        service = await CarWashServiceDAO(session).find_one_or_none_by_id(
            order.service_id
        )

        if not car_wash or not service:
            return

        owner_info = await UserDAO(session).find_one_or_none_by_id(car_wash.owner_id)
        service_data = await ServiceDAO(session).find_one_or_none_by_id(
            service.service_id
        )

        if not user_auto or not user_info or not owner_info or not service_data:
            return

        text = f"""
🔔 <b>НОВЫЙ ЗАКАЗ НА МОЙКУ</b> 🔔

🚗 <b>Автомобиль:</b> {user_auto.brand_id} {user_auto.model_id} / {user_auto.car_number}
👤 <b>Заказ оформил:</b> {user_info.firstname} {user_info.lastname} ({user_info.phone})
🏢 <b>Автомойка:</b> {car_wash.name}
🧼 <b>Услуга:</b> {service_data.name} / {service.price} руб.
🕒 <b>Время заказа:</b> {order.booking_date} {order.booking_time}
"""
        kb = order_rule_keyboard(order, user_info.id)
        await bot.send_message(
            owner_info.telegram_id, text, parse_mode="HTML", reply_markup=kb
        )


@router.post("/create_car")
async def add_new_car(
    car: SCar, session: AsyncSession = Depends(get_session_with_commit)
):
    return await UsersAutosDAO(session).add(car)


@router.post("/check_token")
async def check_token(
    token: str,
    car_wash_id: int,
    session: AsyncSession = Depends(get_session_without_commit),
):
    car_wash = await CarWashDAO(session).find_one_or_none_by_id(car_wash_id)
    if car_wash and str(car_wash.token) == token:
        return True
    return False


@router.post("/add_review")
async def add_review(
    review: SReview, session: AsyncSession = Depends(get_session_with_commit)
):
    car_wash = await CarWashDAO(session).find_one_or_none_by_id(review.car_wash_id)
    if not car_wash:
        return {"error": "Автомойка не найдена"}

    # if car_wash.owner_id != review.user_id:
    #     return {"error": "Вы не можете добавлять отзыв на свою автомойку"}

    new_review = await ReviewDAO(session).add(review)
    now_revies = await ReviewDAO(session).find_all(
        ReviewID(car_wash_id=review.car_wash_id)
    )
    rating = sum(review.rating for review in now_revies) / len(now_revies)
    car_wash.rating = rating
    return {"message": "Отзыв успешно добавлен", "review_id": new_review.id}


@router.get("/reviews/{car_wash_id}")
async def reviews(
    car_wash_id: int, session: AsyncSession = Depends(get_session_without_commit)
):
    query = (
        select(Review)
        .options(joinedload(Review.user))
        .where(Review.car_wash_id == car_wash_id)
    )
    result = await session.execute(query)
    return result.scalars().all()


@router.get("/carwash_terminals/{car_wash_id}/posts")
async def carwash_terminals(
    car_wash_id: int, session: AsyncSession = Depends(get_session_without_commit)
):
    return await WashPostDAO(session).find_all(ReviewID(car_wash_id=car_wash_id))


@router.post("/switch_terminal")
async def switch_terminal(
    post_id: SWatchPostId, session: AsyncSession = Depends(get_session_with_commit)
):
    post_term = await WashPostDAO(session).find_one_or_none_by_id(post_id.id)
    if not post_term:
        return {"error": "Пост не найден"}
    post_term.is_open = not post_term.is_open
    return {"message": "Пост успешно переключен"}


@router.get("/my_bookings/{user_id}")
async def my_bookings(
    user_id: int, session: AsyncSession = Depends(get_session_without_commit)
):
    return await BookingDAO(session).get_user_bookings_full_info(user_id)
