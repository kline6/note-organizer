import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Text, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class ClassificationRule(Base):
    __tablename__ = "classification_rule"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("project.id"), nullable=False)
    pattern: Mapped[str] = mapped_column(String(500), nullable=False)
    target_file: Mapped[str] = mapped_column(String(300), nullable=False)
    priority: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    project = relationship("Project", back_populates="rules")


class HighlightRule(Base):
    __tablename__ = "highlight_rule"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("project.id"), nullable=False)
    pattern: Mapped[str] = mapped_column(String(500), nullable=False)
    color: Mapped[str] = mapped_column(String(50), nullable=False, default="#FF6B6B")
    style: Mapped[str | None] = mapped_column(String(100))
    label: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    project = relationship("Project", back_populates="highlight_rules")
