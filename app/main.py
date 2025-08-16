from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.utils.config import settings
from app.utils.database import create_db_and_tables
from app.handler.exceptions import setup_exception_handlers
from app.route import admin, pay, user, health
from app.utils.logging_config import setup_logging, logger


setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Payment System API")
    await create_db_and_tables()
    logger.success("Database initialized successfully")
    yield
    logger.info("Shutting down Payment System API")

app = FastAPI(
    title="Payment System API",
    description="A secure payment system with user authentication and transaction management",
    version="1.0.0",
    lifespan=lifespan
)

setup_exception_handlers(app)

origins = settings.CORS_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Specify frontend origin(s)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


app.include_router(health.router)
app.include_router(user.router)
app.include_router(pay.router)
if settings.ADMIN_ENABLE:
    logger.warning("Admin features are enabled")
    app.include_router(admin.router)
else:
    logger.warning("Admin features are disabled, skipping admin router inclusion")

logger.info("Payment System API initialized successfully")
