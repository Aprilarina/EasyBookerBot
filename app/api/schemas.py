from pydantic import BaseModel


class ModelMarkID(BaseModel):
    mark_id: str


class UserAutosID(BaseModel):
    user_id: int


class CarWashID(BaseModel):
    car_wash_id: int


class CarWashServiceID(BaseModel):
    car_wash_id: int


class WashPostID(BaseModel):
    car_wash_id: int
    is_open: bool


class SOrder(BaseModel):
    user_id: int
    car_wash_id: int
    service_id: int
    user_auto_id: int
    booking_date: str
    booking_time: str
    status: str = "pending"
    cancellation_reason: str | None = None
    price_at_booking: int
    post_id: int | None = None


class SCar(BaseModel):
    user_id: int
    brand_id: str
    model_id: str
    car_number: str


class SReview(BaseModel):
    user_id: int
    car_wash_id: int
    rating: float
    text: str | None = None


class ReviewID(BaseModel):
    car_wash_id: int


class SWatchPostId(BaseModel):
    id: int
