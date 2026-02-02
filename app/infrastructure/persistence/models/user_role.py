from sqlalchemy import Column, ForeignKey, UUID
from sqlalchemy.orm import relationship

from .base import Base


class UserRole(Base):
    __tablename__ = "user_roles"
    user_id = Column(UUID, ForeignKey("users.id"), primary_key=True)
    role_id = Column(UUID, ForeignKey("roles.id"), primary_key=True)

    user = relationship("User", back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")
