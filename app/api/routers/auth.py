from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, Token
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService

router = APIRouter()

_ERROR = {"description": "Error", "content": {"application/json": {"schema": {"type": "object", "properties": {"detail": {"type": "string"}}}}}}


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=201,
    responses={
        409: {**_ERROR, "description": "Email already registered"},
        422: {**_ERROR, "description": "Validation error"},
    },
)
def register(payload: LoginRequest, db: Session = Depends(get_db)):
    user = AuthService(db).create_user(email=payload.email, password=payload.password)
    return user


@router.post(
    "/login",
    response_model=Token,
    responses={
        401: {**_ERROR, "description": "Invalid email or password"},
        422: {**_ERROR, "description": "Validation error"},
    },
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    service = AuthService(db)
    user = service.authenticate_user(email=form_data.username, password=form_data.password)
    access_token = service.create_access_token_for_user(user)
    return Token(access_token=access_token)


@router.get(
    "/me",
    response_model=UserResponse,
    responses={
        401: {**_ERROR, "description": "Not authenticated or token invalid"},
    },
)
def me(current_user: User = Depends(get_current_user)):
    return current_user
