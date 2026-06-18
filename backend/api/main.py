import logging
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.routers import auth, pipeline, company
from backend.api.routers import health, dashboard
from backend.api.routers.analytics import router as analytics_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="TFG B2B Graph Intelligence API",
    description="Motor analítico de red logística impulsado por Neo4j",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Error no controlado en %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={"message": "Error interno del servidor", "detail": str(exc)},
    )


app.include_router(auth.router)
app.include_router(health.router)
app.include_router(dashboard.router)
app.include_router(analytics_router)
app.include_router(pipeline.router)
app.include_router(company.router)