import uuid

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, Text, UUID, func, text
from sqlalchemy.orm import relationship

from app.core.enums import TaskStatus
from .base import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    task_type = Column(String(50), nullable=False)
    status = Column(Enum(TaskStatus, name="task_status"), nullable=False, default=TaskStatus.queued, index=True)
    model_id = Column(UUID(as_uuid=True), ForeignKey("models.id"), nullable=True)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=True)
    input_path = Column(String(512), nullable=True)
    output_path = Column(String(512), nullable=True)
    error_msg = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="tasks")
    model = relationship("Model", back_populates="tasks")
    dataset = relationship("Dataset", back_populates="tasks")
