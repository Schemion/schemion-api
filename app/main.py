from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

from app.infrastructure.di.container import container
from app.middleware.admin_guard import AdminGuardMiddleware
from app.presentation.routers import admin, auth, datasets, models, tasks, users

app = FastAPI(redirect_slashes=False)

setup_dishka(container=container, app=app)

app.add_middleware(AdminGuardMiddleware)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(tasks.router)
app.include_router(datasets.router)
app.include_router(models.router)
app.include_router(admin.router)

admin.init_admin(app)
