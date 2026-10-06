from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, Enum, ForeignKey, Integer, String, Text

from .db import Base


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum("user", "admin"), nullable=False, default="user")
    plan = Column(Enum("free", "premium"), nullable=False, default="free")
    premium_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utcnow)

    @property
    def is_premium(self) -> bool:
        return self.plan == "premium" and self.premium_until is not None and self.premium_until > utcnow()


class StudySet(Base):
    __tablename__ = "study_sets"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    summary = Column(Text, nullable=False)
    flashcards = Column(JSON, nullable=False)
    quiz = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False, default=utcnow)


class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    payer_phone = Column(String(20), nullable=False)
    amount = Column(Integer, nullable=False)
    currency = Column(String(8), nullable=False, default="UGX")
    reference = Column(String(40), unique=True, nullable=False)
    status = Column(Enum("pending", "approved", "rejected"), nullable=False, default="pending")
    created_at = Column(DateTime, nullable=False, default=utcnow)
    decided_at = Column(DateTime, nullable=True)
