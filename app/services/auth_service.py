from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, db: Session) -> None:
        self.repo = UserRepository(db)

    def create_user(self, email: str, password: str) -> User:
        if self.repo.get_by_email(email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )
        hashed = get_password_hash(password)
        return self.repo.create(email=email, hashed_password=hashed)

    def authenticate_user(self, email: str, password: str) -> User:
        user = self.repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user

    def create_access_token_for_user(self, user: User) -> str:
        return create_access_token(data={"sub": str(user.id)})
