from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, Token
from app.schemas.errors import ErrorResponse
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService

router = APIRouter()

_401 = {"model": ErrorResponse, "description": "Missing, invalid, or expired token."}


@router.post(
    "/register",
    summary="Register a new user",
    description=(
        "Create a new user account with an email and password. "
        "Returns the created user profile. Use `POST /auth/login` to obtain a token."
    ),
    operation_id="register",
    response_model=UserResponse,
    status_code=201,
    responses={
        409: {"model": ErrorResponse, "description": "Email address is already registered."},
        422: {"model": ErrorResponse, "description": "Request body validation error."},
    },
)
def register(payload: LoginRequest, db: Session = Depends(get_db)):
    user = AuthService(db).create_user(email=payload.email, password=payload.password)
    return user


@router.post(
    "/login",
    summary="Log in and obtain a JWT token",
    description=(
        "Authenticate with email and password using the OAuth2 password flow. "
        "Returns a JWT bearer token valid for 30 minutes. "
        "Pass the token as `Authorization: Bearer <token>` on subsequent requests."
    ),
    operation_id="login",
    response_model=Token,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid email or password."},
        422: {"model": ErrorResponse, "description": "Request body validation error."},
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
    summary="Get current user",
    description="Return the profile of the currently authenticated user.",
    operation_id="getCurrentUser",
    response_model=UserResponse,
    responses={401: _401},
)
def me(current_user: User = Depends(get_current_user)):
    return current_user
