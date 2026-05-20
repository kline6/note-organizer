import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Text, Integer, Float, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class NoteFile(Base):
    __tablename__ = "note_file"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("project.id"), nullable=False)
    filename: Mapped[str] = mapped_column(String(300), nullable=False)
    filepath: Mapped[str] = mapped_column(String(500), nullable=False)
    keywords: Mapped[str | None] = mapped_column(String(500))
    summary: Mapped[str | None] = mapped_column(Text)
    color_tag: Mapped[str | None] = mapped_column(String(50))
    created_by_ai: Mapped[bool] = mapped_column(default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    project = relationship("Project", back_populates="note_files")
    entries = relationship("NoteEntry", back_populates="note_file", cascade="all, delete-orphan")


class NoteEntry(Base):
    __tablename__ = "note_entry"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    note_file_id: Mapped[str] = mapped_column(String(36), ForeignKey("note_file.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    highlighted_content: Mapped[str | None] = mapped_column(Text)
    importance: Mapped[str | None] = mapped_column(String(20))
    color: Mapped[str | None] = mapped_column(String(50))
    source_note: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    similarity_score: Mapped[float | None] = mapped_column(Float)
    linked_entry_id: Mapped[str | None] = mapped_column(String(36))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    note_file = relationship("NoteFile", back_populates="entries")
