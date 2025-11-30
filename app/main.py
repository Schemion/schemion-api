from fastapi import FastAPI

from app.container import ApplicationContainer
from app.middleware.admin_guard import AdminGuardMiddleware
from app.presentation.routers import tasks, datasets, users, models, auth, admin, audit_logs

container = ApplicationContainer()
container.config.override({})


app = FastAPI()

app.add_middleware(AdminGuardMiddleware)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(tasks.router)
app.include_router(datasets.router)
app.include_router(models.router)
app.include_router(audit_logs.router)
app.include_router(admin.router)

admin.init_admin(app)