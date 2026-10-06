from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from . import models  # noqa: F401  (registers tables)
from .config import settings
from .db import Base, SessionLocal, engine
from .models import User
from .routes_admin import router as admin_router
from .routes_auth import router as auth_router
from .routes_pay import router as pay_router
from .routes_study import router as study_router
from .security import hash_password

app = FastAPI(title="JAYKAY API", docs_url="/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    resp = await call_next(request)
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Referrer-Policy"] = "no-referrer"
    return resp


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        email = settings.admin_email.lower()
        if not db.query(User).filter(User.email == email).first():
            db.add(User(email=email, password_hash=hash_password(settings.admin_password), role="admin"))
            db.commit()
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "ok", "app": "JAYKAY"}


app.include_router(auth_router)
app.include_router(study_router)
app.include_router(pay_router)
app.include_router(admin_router)
