from uuid import UUID

from sqlalchemy.orm import Session
from typing import Optional

from app.core.enums import UserRole
from app.infrastructure.database import models
from app.presentation import schemas
from app.core.interfaces.user_interface import UserInterface
from app.core.entities.user import User as EntityUser
from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserRepository(UserInterface):
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_email(self, email: str) -> Optional[EntityUser]:
        db_user = self.db.query(models.User).filter(email == models.User.email).first()
        return self._to_entity(db_user) if db_user else None

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
        return self._to_entity(db_user)

    def get_user_by_id(self, user_id: UUID) -> Optional[EntityUser]:
        db_user = self.db.query(models.User).filter(user_id == models.User.id).first()
        return self._to_entity(db_user) if db_user else None



    @staticmethod
    def _to_entity(db_user: models.User) -> EntityUser:
        return EntityUser(
            id=db_user.id,
            email=db_user.email,
            hashed_password=db_user.hashed_password,
            role=db_user.role
        )

    @staticmethod
    def _to_orm(entity: EntityUser) -> models.User:
        return models.User(
            id=entity.id,
            email=entity.email,
            hashed_password=entity.hashed_password,
            role=entity.role
        )