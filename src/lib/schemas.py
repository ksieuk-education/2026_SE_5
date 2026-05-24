from datetime import datetime

from pydantic import BaseModel, Field

from lib.domain import TripStatus


class UserCreate(BaseModel):
    login: str = Field(min_length=1)
    first_name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)


class UserOut(BaseModel):
    id: str
    login: str
    first_name: str
    last_name: str


class TripCreate(BaseModel):
    user_id: str = Field(min_length=1)


class TripAccept(BaseModel):
    driver_id: str = Field(min_length=1)


class TripOut(BaseModel):
    id: str
    user_id: str
    driver_id: str | None
    status: TripStatus
    created_at: datetime | None = None
