from pydantic import BaseModel


class WashOwnerID(BaseModel):
    owner_id: int
