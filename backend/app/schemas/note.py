from pydantic import BaseModel
from datetime import datetime


class NoteFileOut(BaseModel):
    id: str
    project_id: str
    filename: str
    filepath: str
    keywords: str | None = None
    summary: str | None = None
    color_tag: str | None = None
    created_by_ai: bool = False
    sort_order: int = 0
    created_at: datetime
    updated_at: datetime
    entry_count: int = 0

    model_config = {"from_attributes": True}


class NoteEntryOut(BaseModel):
    id: str
    note_file_id: str
    content: str
    highlighted_content: str | None = None
    importance: str | None = None
    color: str | None = None
    source_note: str | None = None
    sort_order: int = 0
    similarity_score: float | None = None
    linked_entry_id: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class EntryMoveRequest(BaseModel):
    entry_id: str
    target_file_id: str


class EntryMergeDecision(BaseModel):
    entry_id: str
    action: str  # merge, replace, skip


class NoteFileUpdate(BaseModel):
    filename: str | None = None
    keywords: str | None = None
    summary: str | None = None
    color_tag: str | None = None
