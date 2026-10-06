import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .config import settings
from .db import get_db
from .models import Payment, User
from .schemas import PaymentRequestIn
from .security import get_current_user

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/request")
def request_upgrade(data: PaymentRequestIn, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    """User asks to go premium. They give THEIR OWN mobile money number.
    The owner's receiving number is never sent to the browser: the owner sees the request in the
    admin dashboard and sends a mobile money payment request to the user (or a payment provider
    API such as MTN MoMo / Flutterwave can be wired in here to push the prompt automatically)."""
    if db.query(Payment).filter(Payment.user_id == user.id, Payment.status == "pending").first():
        raise HTTPException(400, "You already have a pending upgrade request.")
    pay = Payment(user_id=user.id, payer_phone=data.payer_phone, amount=settings.premium_price,
                  currency=settings.currency, reference="JK-" + secrets.token_hex(5).upper())
    db.add(pay)
    db.commit()
    db.refresh(pay)
    return {"reference": pay.reference, "status": pay.status, "amount": pay.amount,
            "currency": pay.currency,
            "message": "Request received. You will get a mobile money payment prompt on your number. "
                       "Premium activates once your payment is confirmed."}


@router.get("/mine")
def my_payments(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(Payment).filter(Payment.user_id == user.id).order_by(Payment.id.desc()).all()
    return [{"reference": r.reference, "status": r.status, "amount": r.amount,
             "currency": r.currency, "created_at": r.created_at.isoformat()} for r in rows]
