import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db, SessionLocal

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("auction")
from app.seed import seed_auction_if_empty
from app.routers import auth, auction


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        seed_auction_if_empty(db)
    finally:
        db.close()
    if settings.smtp_configured:
        log.info("SMTP configured: sending OTP via email (%s)", settings.smtp_user)
    else:
        log.warning("SMTP not configured (set SMTP_USER in .env). OTP will be returned in API response.")
    yield
    # no cleanup needed for sqlite


app = FastAPI(
    title="Auction API",
    description="Private auction backend for the legendary black pouch bag.",
    lifespan=lifespan,
)

_origins = [
    "http://localhost:3000", "http://127.0.0.1:3000",
    "http://localhost:5173", "http://127.0.0.1:5173",
]
if settings.cors_origins:
    _origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(auction.router)


@app.get("/")
def root():
    return {"message": "Auction API. Use /auth/request_otp and /auth/verify_otp to get started."}
