from pydantic import BaseModel


class UserIdModel(BaseModel):
    telegram_id: int


class UserId(BaseModel):
    user_id: int


class UserCreate(UserIdModel):
    username: str | None = None
    firstname: str | None = None
    lastname: str | None = None
    phone: str
