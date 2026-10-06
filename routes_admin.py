from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .config import settings
from .db import get_db
from .models import Payment, User, utcnow
from .security import require_admin

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/settings")
def owner_settings(_: User = Depends(require_admin)):
    # The ONLY place the owner's payment number is ever returned.
    return {"owner_payment_number": settings.owner_payment_number}


@router.get("/users")
def users(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.query(User).order_by(User.id.desc()).limit(500).all()
    return [{"id": u.id, "email": u.email, "role": u.role,
             "plan": "premium" if u.is_premium else "free",
             "premium_until": u.premium_until.isoformat() if u.premium_until else None} for u in rows]


@router.get("/payments")
def payments(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.query(Payment, User.email).join(User, User.id == Payment.user_id)\
             .order_by(Payment.id.desc()).limit(500).all()
    return [{"id": p.id, "email": e, "payer_phone": p.payer_phone, "amount": p.amount,
             "currency": p.currency, "reference": p.reference, "status": p.status,
             "created_at": p.created_at.isoformat()} for p, e in rows]


def _decide(db: Session, pay_id: int, status: str) -> Payment:
    pay = db.get(Payment, pay_id)
    if not pay or pay.status != "pending":
        raise HTTPException(400, "Payment not found or already decided.")
    pay.status, pay.decided_at = status, utcnow()
    return pay


@router.post("/payments/{pay_id}/approve")
def approve(pay_id: int, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    pay = _decide(db, pay_id, "approved")
    user = db.get(User, pay.user_id)
    start = user.premium_until if user.premium_until and user.premium_until > utcnow() else utcnow()
    user.plan, user.premium_until = "premium", start + timedelta(days=settings.premium_days)
    db.commit()
    return {"ok": True}


@router.post("/payments/{pay_id}/reject")
def reject(pay_id: int, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    _decide(db, pay_id, "rejected")
    db.commit()
    return {"ok": True}
