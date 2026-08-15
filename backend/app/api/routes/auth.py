from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ...db import get_db
from ...models.auth import Account, AuthSession
from ...schemas.auth import LoginRequest, LoginResponse, LogoutResponse
from ...services.auth import generate_session_token, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    account = db.query(Account).filter(Account.username == payload.username).first()
    if account is None or not verify_password(payload.password, account.password_hash):
        raise HTTPException(status_code=401, detail="账号或密码错误")

    token = generate_session_token()
    db.add(AuthSession(token=token, username=account.username))
    db.commit()
    return LoginResponse(token=token, username=account.username)


@router.post("/logout", response_model=LogoutResponse)
def logout(request: Request, db: Session = Depends(get_db)) -> LogoutResponse:
    token = getattr(request.state, "session_token", None)
    if token:
        db.query(AuthSession).filter(AuthSession.token == token).delete()
        db.commit()
    return LogoutResponse(message="已退出登录")
