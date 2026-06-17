from datetime import datetime

from pydantic import BaseModel, field_validator


class CategoryCreate(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def normalize(cls, v: str) -> str:
        return v.strip().title()


class CategoryUpdate(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def normalize(cls, v: str) -> str:
        return v.strip().title()


class CategoryResponse(BaseModel):
    id: int
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}
