from sqladmin import ModelView

from app.infrastructure.persistence.models import Dataset


class DatasetAdmin(ModelView, model=Dataset):
    column_list = [Dataset.id, Dataset.name, Dataset.description]
