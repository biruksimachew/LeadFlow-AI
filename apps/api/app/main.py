import asyncio
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, HTTPException, Request, status

from app.database import (
    create_database_pool,
    database_is_alive,
)
from app.routers.leads import router as leads_router
from app.providers.crm.factory import (
    build_crm_provider,
)
from app.providers.crm.base import (
    CRMProviderError,
)
from app.routers.webhooks import (
    router as webhooks_router,
)
from app.routers.overrides import (
    router as overrides_router,
)

from app.routers.retries import (
    router as retries_router,
)
from app.routers.orchestration import (
    router as orchestration_router,
)
from app.config import settings
from app.services.retry_worker import (
    WorkflowRetryWorker,
)
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db_pool = (
        await create_database_pool()
    )
    app.state.retry_worker = None
    app.state.retry_worker_task = None

    if settings.workflow_retry_enabled:
        retry_worker = WorkflowRetryWorker(
            app.state.db_pool
        )
        retry_task = asyncio.create_task(
            retry_worker.run_forever(),
            name="leadflow-workflow-retry-worker",
        )

        app.state.retry_worker = retry_worker
        app.state.retry_worker_task = retry_task

    try:
        yield
    finally:
        retry_worker = (
            app.state.retry_worker
        )
        retry_task = (
            app.state.retry_worker_task
        )

        if retry_worker is not None:
            await retry_worker.stop()

        if retry_task is not None:
            with suppress(asyncio.CancelledError):
                await retry_task

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




@app.get(
    "/health/retry-worker",
    tags=["System"],
)
async def retry_worker_health(
    request: Request,
) -> dict[str, str | bool]:
    task = request.app.state.retry_worker_task

    if not settings.workflow_retry_enabled:
        return {
            "status": "disabled",
            "enabled": False,
            "running": False,
        }

    running = bool(
        task is not None
        and not task.done()
    )

    if not running:
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail="Retry worker is not running.",
        )

    return {
        "status": "ok",
        "enabled": True,
        "running": True,
    }


@app.get(
    "/health/hubspot",
    tags=["System"],
)
async def hubspot_health() -> dict[str, str]:

    provider = None

    try:

        provider = build_crm_provider()

        healthy = await provider.health_check()

        if not healthy:
            raise HTTPException(
                status_code=503,
                detail="HubSpot unavailable.",
            )

        return {
            "status": "ok",
            "hubspot": "reachable",
        }

    except CRMProviderError as exc:

        raise HTTPException(
            status_code=503,
            detail={
                "code": exc.code,
                "message": exc.message,
            },
        ) from exc

    finally:

        if (
            provider is not None
            and hasattr(provider, "close")
        ):
            await provider.close()

app.include_router(leads_router)
app.include_router(webhooks_router)
app.include_router(
    overrides_router
)
app.include_router(
    retries_router
)
app.include_router(
    orchestration_router
)
