import asyncio

from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from app.core.exceptions import NotFoundError, ServiceUnavailableError, UnauthorizedError, ValidationError
from app.infrastructure.di.container import container
from app.infrastructure.config import settings
from app.infrastructure.services.broker import BobberTaskStatusConsumer
from app.middleware.admin_guard import AdminGuardMiddleware
from app.presentation.routers import admin, auth, datasets, models, tasks

from fastapi.middleware.cors import CORSMiddleware

from app.infrastructure.rate_limiter import init_rate_limiter

app = FastAPI(redirect_slashes=True)
init_rate_limiter(app)


@app.on_event("startup")
async def start_task_status_consumer():
    consumer = BobberTaskStatusConsumer(
        host=settings.BOBBER_HOST or "localhost",
        port=settings.BOBBER_PORT or 50051,
        loop=asyncio.get_running_loop(),
    )
    consumer.start()
    app.state.task_status_consumer = consumer


@app.on_event("shutdown")
async def stop_task_status_consumer():
    consumer = getattr(app.state, "task_status_consumer", None)
    if consumer:
        consumer.close()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(NotFoundError)
async def not_found_error_handler(_, exc: NotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})

@app.exception_handler(UnauthorizedError)
async def unauthorized_error_handler(_, exc: UnauthorizedError):
    return JSONResponse(status_code=401, content={"detail": str(exc)})

@app.exception_handler(ValidationError)
async def validation_error_handler(_, exc: ValidationError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})

@app.exception_handler(ServiceUnavailableError)
async def service_unavailable_error_handler(_, exc: ServiceUnavailableError):
    return JSONResponse(status_code=503, content={"detail": str(exc)})

setup_dishka(container=container, app=app)

app.add_middleware(AdminGuardMiddleware)

app.include_router(auth.router)
app.include_router(tasks.router)
app.include_router(datasets.router)
app.include_router(models.router)
app.include_router(admin.router)

admin.init_admin(app)
