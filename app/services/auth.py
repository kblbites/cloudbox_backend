from sqlalchemy.orm import Session

from app.core.exceptions import CloudBoxError
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models import User
from app.schemas.auth import UserLogin, UserRegister
from fastapi import status


class AuthService:
    def register(self, db: Session, payload: UserRegister) -> User:
        existing = db.query(User).filter(User.email == payload.email.lower()).first()
        if existing:
            raise CloudBoxError("Email already registered", status_code=status.HTTP_400_BAD_REQUEST)
        user = User(
            email=payload.email.lower(),
            full_name=payload.full_name.strip(),
            hashed_password=hash_password(payload.password),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def login(self, db: Session, payload: UserLogin) -> tuple[User, str]:
        user = db.query(User).filter(User.email == payload.email.lower()).first()
        if not user or not verify_password(payload.password, user.hashed_password):
            raise CloudBoxError(
                "Invalid email or password",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        token = create_access_token(str(user.id))
        return user, token

    def get_user(self, db: Session, user_id: int) -> User:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise CloudBoxError("User not found", status_code=status.HTTP_404_NOT_FOUND)
        return user
