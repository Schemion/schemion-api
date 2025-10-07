import uuid

from sqlalchemy import Column, UUID, String, Text, Integer, DateTime, func
from sqlalchemy.orm import relationship

from app.infrastructure.database.models.base import Base


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    minio_path = Column(String(512), nullable=False)
    description = Column(Text, nullable=True)
    num_samples = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    models = relationship("Model", back_populates="dataset")
    tasks = relationship("Task", back_populates="dataset")
