from fastapi import APIRouter, Depends

from app.api.deps import get_auth_service, get_current_user
from app.core.exceptions import CloudBoxError, to_http_exception
from app.db.database import get_db
from app.db.models import User
from app.schemas.auth import TokenResponse, UserLogin, UserOut, UserRegister
from app.services.auth import AuthService
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(
    payload: UserRegister,
    db: Session = Depends(get_db),
    auth: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    try:
        from app.core.security import create_access_token

        user = auth.register(db, payload)
        token = create_access_token(str(user.id))
        return TokenResponse(access_token=token)
    except CloudBoxError as exc:
        raise to_http_exception(exc) from exc


@router.post("/login", response_model=TokenResponse)
def login(
    payload: UserLogin,
    db: Session = Depends(get_db),
    auth: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    try:
        _user, token = auth.login(db, payload)
        return TokenResponse(access_token=token)
    except CloudBoxError as exc:
        raise to_http_exception(exc) from exc


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(current_user)
