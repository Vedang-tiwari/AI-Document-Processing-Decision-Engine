import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy import text

from backend.app.core.config import settings
from backend.app.core.logging import setup_logging, logger, correlation_request_id
from backend.app.core.exceptions import AppException
from backend.app.db.session import engine, SessionLocal
from backend.app.db.base import Base
import backend.app.db.models  # ensure models are registered

# Include API v1 routers
from backend.app.api.v1.documents import router as documents_router
from backend.app.api.v1.reviews import router as reviews_router
from backend.app.api.v1.rules import router as rules_router
from backend.app.api.v1.webhooks import router as webhooks_router
from backend.app.api.v1.dashboard import router as dashboard_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(settings.LOG_LEVEL)
    logger.info(f"Starting {settings.APP_NAME} in '{settings.APP_ENV}' mode.")
    # Ensure tables exist (helpful for local sqlite without running alembic manually)
    Base.metadata.create_all(bind=engine)
    yield
    logger.info(f"Shutting down {settings.APP_NAME}.")


app = FastAPI(
    title="AI Document Processing & Decision Engine",
    description="Production-grade AI document processing, OCR, validation, business rules, and human review system.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Correlation & Request ID Middleware
@app.middleware("http")
async def correlation_middleware(request: Request, call_next):
    req_id = request.headers.get("X-Request-Id", str(uuid.uuid4()))
    correlation_request_id.set(req_id)
    response = await call_next(request)
    response.headers["X-Request-Id"] = req_id
    return response


# Standardized Error Handlers
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    req_id = correlation_request_id.get() or str(uuid.uuid4())
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "request_id": req_id,
                "details": exc.details,
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    req_id = correlation_request_id.get() or str(uuid.uuid4())
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "The request payload failed schema validation.",
                "request_id": req_id,
                "details": exc.errors(),
            }
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    req_id = correlation_request_id.get() or str(uuid.uuid4())
    logger.exception(f"Unhandled server error [request_id={req_id}]: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred while processing the request.",
                "request_id": req_id,
            }
        },
    )


# Health Check Endpoints (Section 18)
@app.get("/health/live", tags=["Health"], summary="Liveness check")
def health_live():
    return {"status": "ok", "service": "document_engine"}


@app.get("/health/ready", tags=["Health"], summary="Readiness check verifying DB connectivity")
def health_ready():
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unavailable", "database": "disconnected", "error": str(e)},
        )
    finally:
        db.close()


# Mount v1 API Routers
api_v1_prefix = settings.API_V1_PREFIX
app.include_router(documents_router, prefix=api_v1_prefix)
app.include_router(reviews_router, prefix=api_v1_prefix)
app.include_router(rules_router, prefix=api_v1_prefix)
app.include_router(webhooks_router, prefix=api_v1_prefix)
app.include_router(dashboard_router, prefix=api_v1_prefix)
