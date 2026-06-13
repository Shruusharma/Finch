import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from core.exceptions import FinchError
from config import settings
from api.routes import chat, insights
from memory.vector_store import add_portfolio_chunks
from memory.portfolio_data import SAMPLE_PORTFOLIO, portfolio_to_chunks

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Autonomous Wealth Assistant API"
)

app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
app.include_router(insights.router, prefix="/api/v1", tags=["insights"])

@app.exception_handler(FinchError)
async def finch_error_handler(request: Request, exc: FinchError):
    logger.error(f"{type(exc).__name__}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": type(exc).__name__,
            "detail": exc.detail,
        },
    )

@app.on_event("startup")
async def startup_event():
    logger.info("Seeding portfolio vector store...")
    chunks = portfolio_to_chunks(SAMPLE_PORTFOLIO)
    add_portfolio_chunks(chunks)
    logger.info(f"Seeded {len(chunks)} portfolio positions")


@app.get("/health")
async def health():
    logger.info("Health check called")
    return {
        "status": "ok",
        "app": settings.app_name,
        "env": settings.app_env
    }