from uuid import UUID

from sqlalchemy.orm import Session
from typing import Optional

from app.core.enums import UserRole
from app.infrastructure.database import models
from app.presentation import schemas
from app.core.interfaces.user_interface import UserInterface
from app.core.entities.user import User as EntityUser
from passlib.context import CryptContext
from app.infrastructure.mappers import OrmEntityMapper


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserRepository(UserInterface):
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

