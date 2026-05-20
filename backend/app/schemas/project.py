from pydantic import BaseModel
from datetime import datetime


class ProjectCreate(BaseModel):
    name: str


class ProjectOut(BaseModel):
    id: str
    name: str
    workspace_dir: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
