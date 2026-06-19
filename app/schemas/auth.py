from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Token(BaseModel):
    access_token: str = Field(..., description="JWT bearer token to include in the Authorization header.")
    token_type: str = Field("bearer", description="Token type — always 'bearer'.")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIn0.abc123",
                "token_type": "bearer",
            }
        }
    )


class TokenData(BaseModel):
    user_id: int


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User's registered email address.")
    password: str = Field(..., description="Account password.")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "password123",
            }
        }
    )
