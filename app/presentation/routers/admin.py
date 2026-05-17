from fastapi import APIRouter
from sqladmin import Admin

from app.common.admin import AdminAuth
from app.common.admin.models import DatasetAdmin, ModelAdmin, TaskAdmin, UserAdmin
from app.infrastructure.config import settings
from app.infrastructure.database import engine


def _normalize_admin_base_url(path: str) -> str:
    normalized = (path or "/admin").strip()
    if not normalized.startswith("/"):
        normalized = f"/{normalized}"
    normalized = normalized.rstrip("/")
    return normalized or "/admin"


ADMIN_BASE_URL = _normalize_admin_base_url(settings.ADMIN_BASE_URL)

router = APIRouter(prefix=ADMIN_BASE_URL, tags=["admin"])


def init_admin(app):
    admin = Admin(
        app=app,
        engine=engine,
        base_url=ADMIN_BASE_URL,
        authentication_backend=AdminAuth(),
    )
    admin.add_view(UserAdmin)
    admin.add_view(DatasetAdmin)
    admin.add_view(TaskAdmin)
    admin.add_view(ModelAdmin)
    return admin
