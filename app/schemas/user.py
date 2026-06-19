from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserResponse(BaseModel):
    id: int = Field(..., description="Unique user identifier.")
    email: EmailStr = Field(..., description="User's email address.")
    created_at: datetime = Field(..., description="UTC timestamp when the account was created.")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "email": "user@example.com",
                "created_at": "2026-06-01T10:00:00",
            }
        },
    )
