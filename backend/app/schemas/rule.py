from pydantic import BaseModel
from datetime import datetime


class ClassificationRuleCreate(BaseModel):
    project_id: str
    pattern: str
    target_file: str
    priority: int = 0


class ClassificationRuleOut(BaseModel):
    id: str
    project_id: str
    pattern: str
    target_file: str
    priority: int
    created_at: datetime

    model_config = {"from_attributes": True}


class HighlightRuleCreate(BaseModel):
    project_id: str
    pattern: str
    color: str = "#FF6B6B"
    style: str | None = None
    label: str | None = None


class HighlightRuleOut(BaseModel):
    id: str
    project_id: str
    pattern: str
    color: str
    style: str | None = None
    label: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ClassifyRequest(BaseModel):
    project_id: str
    summary_text: str
