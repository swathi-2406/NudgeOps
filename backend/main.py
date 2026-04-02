"""
NudgeOps — MLOps Platform for Personalized Behavioral Intervention Policies
FastAPI application entrypoint
"""
from contextlib import asynccontextmanager
import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from prometheus_client import make_asgi_app

from core.config import settings
from core.logging import configure_logging
from db.database import engine, Base
from db.seed import seed_initial_data
from api.routes import users, events, interventions, bandit, policies, experiments, monitoring, features, audit
from api.middleware.logging import LoggingMiddleware
from api.middleware.metrics import MetricsMiddleware

configure_logging()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("nudgeops_starting", version=settings.VERSION, env=settings.ENVIRONMENT)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("database_tables_created")
    await seed_initial_data()
    logger.info("initial_data_seeded")
    yield
    logger.info("nudgeops_shutting_down")
    await engine.dispose()


app = FastAPI(
    title="NudgeOps API",
    description=(
        "MLOps platform for personalized behavioral intervention policies.\n\n"
        "Features: Contextual bandit, user embeddings, A/B testing, "
        "policy registry, monitoring, fairness checks, audit logging."
    ),
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(LoggingMiddleware)
app.add_middleware(MetricsMiddleware)

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

app.include_router(users.router,         prefix="/api/v1/users",         tags=["Users"])
app.include_router(events.router,        prefix="/api/v1/events",        tags=["Events"])
app.include_router(interventions.router, prefix="/api/v1/interventions", tags=["Interventions"])
app.include_router(bandit.router,        prefix="/api/v1/bandit",        tags=["Bandit Engine"])
app.include_router(policies.router,      prefix="/api/v1/policies",      tags=["Policy Registry"])
app.include_router(experiments.router,   prefix="/api/v1/experiments",   tags=["A/B Testing"])
app.include_router(monitoring.router,    prefix="/api/v1/monitoring",    tags=["Monitoring"])
app.include_router(features.router,      prefix="/api/v1/features",      tags=["Feature Store"])
app.include_router(audit.router,         prefix="/api/v1/audit",         tags=["Audit Logs"])


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "version": settings.VERSION, "environment": settings.ENVIRONMENT}


@app.get("/", tags=["Root"])
async def root():
    return {"name": "NudgeOps API", "version": settings.VERSION, "docs": "/docs", "metrics": "/metrics"}
