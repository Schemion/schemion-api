import uuid

from sqlalchemy import Column, String, UUID, text
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import relationship

from .base import Base


class Permission(Base):
    __tablename__ = 'permissions'
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), default=uuid.uuid4)
    name = Column(String(30), unique=True)
    resource = Column(String(30))

    role_permissions = relationship("RolePermission", back_populates="permission")
    roles = association_proxy("role_permissions", "role")
