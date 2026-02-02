from sqlalchemy import Column, ForeignKey, UUID
from sqlalchemy.orm import relationship

from .base import Base


class RolePermission(Base):
    __tablename__ = "role_permissions"
    role_id = Column(UUID, ForeignKey("roles.id"), primary_key=True)
    permission_id = Column(UUID, ForeignKey("permissions.id"), primary_key=True)

    role = relationship("Role", back_populates="role_permissions")
    permission = relationship("Permission", back_populates="role_permissions")
