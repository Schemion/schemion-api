import uuid

from sqlalchemy import Column, UUID, String, ForeignKey, func, DateTime, Enum
from sqlalchemy.orm import relationship

from app.core.enums import ModelStatus
from app.infrastructure.database.models.base import Base


class Model(Base):
    __tablename__ = "models"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    version = Column(String(50), nullable=False)
    architecture = Column(String(50), nullable=False)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=True)
    minio_model_path = Column(String(512), nullable=False)
    status = Column(Enum(ModelStatus, name="model_status"), nullable=False, default=ModelStatus.pending)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    dataset = relationship("Dataset", back_populates="models")
    tasks = relationship("Task", back_populates="model")
