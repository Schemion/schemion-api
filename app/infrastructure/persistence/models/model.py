import uuid

from sqlalchemy import ARRAY, Boolean, Column, DateTime, Enum, ForeignKey, String, Text, UUID, func, text
from sqlalchemy.orm import relationship

from .base import Base


class Model(Base):
    __tablename__ = "models"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    architecture = Column(String(50), nullable=False)
    architecture_profile = Column(String(512), nullable=False)  # resnet или еще что-то
    classes = Column(ARRAY(Text), nullable=True)
    minio_model_path = Column(String(512), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    is_system = Column(Boolean, default=False, nullable=False)
    base_model_id = Column(UUID(as_uuid=True), ForeignKey("models.id"), nullable=True)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    dataset = relationship("Dataset", back_populates="models")
    tasks = relationship("Task", back_populates="model")
    base_model = relationship("Model", remote_side=[id], backref="derived_models")
    user = relationship("User", back_populates="models")
