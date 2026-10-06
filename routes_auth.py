from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from .config import settings
from .db import get_db
from .models import StudySet, User
from .schemas import LoginIn, RegisterIn
from .security import (check_login_allowed, clear_login_failures, create_token, get_current_user,
                       hash_password, record_login_failure, verify_password)

router = APIRouter(prefix="/auth", tags=["auth"])


def limits_for(user: User):
    if user.is_premium:
        return settings.premium_daily_limit, settings.premium_max_chars
    return settings.free_daily_limit, settings.free_max_chars


def used_today(db: Session, user: User) -> int:
    start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
    return db.query(func.count(StudySet.id)).filter(
        StudySet.user_id == user.id, StudySet.created_at >= start).scalar() or 0


def public_user(db: Session, user: User) -> dict:
    daily, max_chars = limits_for(user)
    return {
        "id": user.id, "email": user.email, "role": user.role,
        "plan": "premium" if user.is_premium else "free",
        "premium_until": user.premium_until.isoformat() if user.premium_until else None,
        "daily_limit": daily, "used_today": used_today(db, user), "max_chars": max_chars,
        "premium_price": settings.premium_price, "currency": settings.currency,
    }  # NOTE: the owner payment number is never included here


@router.post("/register")
def register(data: RegisterIn, db: Session = Depends(get_db)):
    email = data.email.lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(400, "Could not create account with those details.")
    user = User(email=email, password_hash=hash_password(data.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"token": create_token(user.id), "user": public_user(db, user)}


@router.post("/login")
def login(data: LoginIn, request: Request, db: Session = Depends(get_db)):
    email = data.email.lower()
    key = f"{email}|{request.client.host if request.client else 'x'}"
    check_login_allowed(key)
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(data.password, user.password_hash):
        record_login_failure(key)
        raise HTTPException(401, "Wrong email or password.")
    clear_login_failures(key)
    return {"token": create_token(user.id), "user": public_user(db, user)}


@router.get("/me")
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return public_user(db, user)
