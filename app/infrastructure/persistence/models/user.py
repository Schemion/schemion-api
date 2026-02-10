import uuid

from sqlalchemy import Column, DateTime, String, UUID, func, text
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import relationship

from .base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tasks = relationship("Task", back_populates="user")
    datasets = relationship("Dataset", back_populates="user", cascade="all, delete-orphan")
    models = relationship("Model", back_populates="user", cascade="all, delete-orphan")
    user_roles = relationship("UserRole", back_populates="user", lazy="selectin")

    roles = association_proxy("user_roles", "role")
