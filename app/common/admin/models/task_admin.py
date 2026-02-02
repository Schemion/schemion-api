from sqladmin import ModelView

from app.infrastructure.persistence.models import Task


class TaskAdmin(ModelView, model=Task):
    column_list = [Task.id, Task.task_type, Task.error_msg]
