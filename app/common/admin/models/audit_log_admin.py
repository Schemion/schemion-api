from sqladmin import ModelView
from app.infrastructure.database.models import AuditLog

class AuditLogAdmin(ModelView, model=AuditLog):
    column_list = [AuditLog.id, AuditLog.action, AuditLog.details]