import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Project(Base):
    __tablename__ = "project"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    workspace_dir: Mapped[str | None] = mapped_column(String(500))
    session_key: Mapped[str] = mapped_column(String(100), default="default", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    note_files = relationship("NoteFile", back_populates="project", cascade="all, delete-orphan")
    rules = relationship("ClassificationRule", back_populates="project", cascade="all, delete-orphan")
    highlight_rules = relationship("HighlightRule", back_populates="project", cascade="all, delete-orphan")
    snapshots = relationship("Snapshot", back_populates="project", cascade="all, delete-orphan")
