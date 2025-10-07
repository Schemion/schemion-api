from sqladmin import ModelView
from app.infrastructure.database.models import Dataset

class DatasetAdmin(ModelView, model=Dataset):
    column_list = [Dataset.id, Dataset.name, Dataset.description, Dataset.num_samples]