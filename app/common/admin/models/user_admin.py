from sqladmin import ModelView

from app.infrastructure.persistence.models import User


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.email, User.roles]
