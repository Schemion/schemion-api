import uuid

from sqlalchemy import Column, String, UUID, text
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import relationship

from .base import Base


class Role(Base):
    __tablename__ = 'roles'
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), default=uuid.uuid4)
    name = Column(String(30), unique=True)

    user_roles = relationship("UserRole", back_populates="role")
    role_permissions = relationship("RolePermission", back_populates="role", lazy="selectin")

    users = association_proxy("user_roles", "user")
    permissions = association_proxy("role_permissions", "permission")
