from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CategoryCreate(BaseModel):
    name: str = Field(..., description="Category name. Normalised to title case on save.")

    @field_validator("name")
    @classmethod
    def normalize(cls, v: str) -> str:
        return v.strip().title()

    model_config = ConfigDict(
        json_schema_extra={"example": {"name": "Food"}}
    )


class CategoryUpdate(BaseModel):
    name: str = Field(..., description="New category name. Normalised to title case on save.")

    @field_validator("name")
    @classmethod
    def normalize(cls, v: str) -> str:
        return v.strip().title()

    model_config = ConfigDict(
        json_schema_extra={"example": {"name": "Transport"}}
    )


class CategoryResponse(BaseModel):
    id: int = Field(..., description="Unique category identifier.")
    name: str = Field(..., description="Category name.")
    created_at: datetime = Field(..., description="UTC timestamp when the category was created.")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 3,
                "name": "Food",
                "created_at": "2026-06-01T10:00:00",
            }
        },
    )
