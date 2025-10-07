from sqladmin import ModelView
from app.infrastructure.database.models import Task

class TaskAdmin(ModelView, model=Task):
    column_list = [Task.id, Task.task_type, Task.error_msg]