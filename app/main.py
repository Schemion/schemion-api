from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from app.core.exceptions import NotFoundError, UnauthorizedError, ValidationError
from app.infrastructure.di.container import container
from app.middleware.admin_guard import AdminGuardMiddleware
from app.presentation.routers import admin, auth, datasets, models, tasks, users

app = FastAPI(redirect_slashes=False)

@app.exception_handler(NotFoundError)
async def not_found_error_handler(_, exc: NotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})

@app.exception_handler(UnauthorizedError)
async def unauthorized_error_handler(_, exc: UnauthorizedError):
    return JSONResponse(status_code=401, content={"detail": str(exc)})

@app.exception_handler(ValidationError)
async def validation_error_handler(_, exc: ValidationError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})

setup_dishka(container=container, app=app)

app.add_middleware(AdminGuardMiddleware)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(tasks.router)
app.include_router(datasets.router)
app.include_router(models.router)
app.include_router(admin.router)

admin.init_admin(app)
