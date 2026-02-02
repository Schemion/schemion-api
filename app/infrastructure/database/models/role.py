from sqlalchemy import Column, Integer, String, UUID
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import relationship

from .base import Base


class Role(Base):
    __tablename__ = 'roles'
    id = Column(UUID, primary_key=True)
    name = Column(String(30), unique=True)

    user_roles = relationship("UserRole", back_populates="role")
    role_permissions = relationship("RolePermission", back_populates="role", lazy="selectin")

    users = association_proxy("user_roles", "user")
    permissions = association_proxy("role_permissions", "permission")
