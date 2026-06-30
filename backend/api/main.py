"""Punto de entrada de la aplicación FastAPI.

Crea la instancia ``app``, registra el middleware CORS, el manejador global
de excepciones y monta todos los routers del sistema.

Arranque en desarrollo::

    uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000
"""
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
    docs_url="/swagger",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Captura cualquier excepción no controlada y devuelve un 500 estructurado.

    Evita que los stack traces internos lleguen al cliente en texto plano.
    Todos los errores se registran con ``logger.error`` para trazabilidad.

    Args:
        request: Petición HTTP que originó la excepción.
        exc: Excepción no capturada por ningún handler específico.

    Returns:
        JSONResponse: HTTP 500 con ``message`` y ``detail`` del error.
    """
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