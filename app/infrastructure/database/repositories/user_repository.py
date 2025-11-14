from uuid import UUID

from sqlalchemy.orm import Session
from typing import Optional, List

from app.core.enums import UserRole
from app.infrastructure.database import models
from app.presentation import schemas
from app.core.interfaces.user_interface import IUserRepository
from app.core.entities.dataset import Dataset as EntityDataset
from app.core.entities.model import Model as EntityModel
from app.core.entities.user import User as EntityUser
from passlib.context import CryptContext
from app.infrastructure.mappers import OrmEntityMapper


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserRepository(IUserRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_email(self, email: str) -> Optional[EntityUser]:
        db_user = self.db.query(models.User).filter(email == models.User.email).first()
        return OrmEntityMapper.to_entity(db_user, EntityUser) if db_user else None

    def create_user(self, user: schemas.UserCreate) -> EntityUser:
        hashed_password = pwd_context.hash(user.password)
        db_user = models.User(
            email=user.email,
            hashed_password=hashed_password,
            role = UserRole.user
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return OrmEntityMapper.to_entity(db_user, EntityUser)

    def get_user_by_id(self, user_id: UUID) -> Optional[EntityUser]:
        db_user = self.db.query(models.User).filter(user_id == models.User.id).first()
        return OrmEntityMapper.to_entity(db_user, EntityUser) if db_user else None

    def get_user_datasets(self, user_id: UUID) -> List[EntityDataset]:
        db_datasets = (
            self.db.query(models.Dataset)
            .filter(models.Dataset.user_id == user_id)
            .all()
        )
        return [OrmEntityMapper.to_entity(d, EntityDataset) for d in db_datasets]

    def get_user_models(self, user_id: UUID) -> List[EntityModel]:
        db_models = (
            self.db.query(models.Model)
            .filter(
                models.Model.user_id == user_id,
                models.Model.is_system == False
            )
            .all()
        )
        return [OrmEntityMapper.to_entity(m, EntityModel) for m in db_models]

