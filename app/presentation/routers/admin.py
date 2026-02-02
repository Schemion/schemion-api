from fastapi import APIRouter
from sqladmin import Admin

from app.common.admin import AdminAuth
from app.common.admin.models import DatasetAdmin, ModelAdmin, TaskAdmin, UserAdmin
from app.infrastructure.database import engine

router = APIRouter(prefix="/admin", tags=["admin"])


def init_admin(app):
    admin = Admin(app=app, engine=engine, authentication_backend=AdminAuth())
    admin.add_view(UserAdmin)
    admin.add_view(DatasetAdmin)
    admin.add_view(TaskAdmin)
    admin.add_view(ModelAdmin)
    return admin
