from datetime import datetime

from pydantic import Field

from app.schemas.common import ORMModel


class UserBase(ORMModel):
    username: str = Field(min_length=3, max_length=50)


class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=128)


class UserRead(UserBase):
    id: int
    created_at: datetime


class UserInDB(UserRead):
    password_hash: str
