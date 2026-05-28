import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .app.core.config import settings
from .app.core.database import init_db
from .app.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("STACK Service Desk API starting up...")
    try:
        await init_db()
        logger.info("Database tables ensured")
        from .app.utils.seed import seed_initial_data
        await seed_initial_data()
        logger.info("Seed data complete")
    except Exception as e:
        logger.error(f"Startup error: {e}")
    yield
    logger.info("STACK Service Desk API shutting down")


app = FastAPI(
    title="STACK Service Desk AI Solution",
    description="Enterprise IT Service Desk API for Jade Global Software",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get("/api/healthz")
async def healthz():
    return {"status": "ok"}


from .app.api.v1.routes.auth import router as auth_router
from .app.api.v1.routes.tickets import router as tickets_router
from .app.api.v1.routes.dashboard import router as dashboard_router
from .app.api.v1.routes.admin import router as admin_router
from .app.api.v1.routes.sops import router as sops_router
from .app.api.v1.routes.reports import router as reports_router
from .app.api.v1.routes.roi import router as roi_router
from .app.api.v1.routes.logs import router as logs_router
from .app.api.v1.routes.chat import router as chat_router

app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(tickets_router, prefix="/api/v1/tickets", tags=["tickets"])
app.include_router(dashboard_router, prefix="/api/v1/dashboard", tags=["dashboard"])
app.include_router(admin_router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(sops_router, prefix="/api/v1/sops", tags=["sops"])
app.include_router(reports_router, prefix="/api/v1/reports", tags=["reports"])
app.include_router(roi_router, prefix="/api/v1/roi", tags=["roi"])
app.include_router(logs_router, prefix="/api/v1/logs", tags=["logs"])
app.include_router(chat_router, prefix="/api/v1/chat", tags=["chat"])


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.url}: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
