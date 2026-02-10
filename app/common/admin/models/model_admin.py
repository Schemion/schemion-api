from sqladmin import ModelView

from app.infrastructure.persistence.models import Model


class ModelAdmin(ModelView, model=Model):
    column_list = [Model.id, Model.name, Model.dataset_id]
