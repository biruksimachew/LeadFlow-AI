from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status

from app.database import (
    create_database_pool,
    database_is_alive,
)
from app.routers.leads import router as leads_router


@asynccontextmanager
async def lifespan(app: FastAPI):

    app.state.db_pool = await create_database_pool()

    yield

    await app.state.db_pool.close()


app = FastAPI(
    title="LeadFlow AI API",
    description=(
        "AI-assisted lead intake and sales operations "
        "automation platform."
    ),
    version="0.3.0",
    lifespan=lifespan,
)


@app.get(
    "/health",
    tags=["System"],
)
async def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "leadflow-api",
    }


@app.get(
    "/health/database",
    tags=["System"],
)
async def database_health(
    request: Request,
) -> dict[str, str]:

    try:
        healthy = await database_is_alive(
            request.app.state.db_pool
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable.",
        ) from exc

    if not healthy:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable.",
        )

    return {
        "status": "ok",
        "database": "reachable",
    }


app.include_router(leads_router)