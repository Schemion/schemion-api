from sqladmin import ModelView
from app.infrastructure.database.models import Model

class ModelAdmin(ModelView, model=Model):
    column_list = [Model.id, Model.name, Model.version, Model.dataset_id, Model.status]