import os
import uuid
import traceback
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.project import Project
from app.models.note import NoteFile, NoteEntry
from app.schemas.project import ProjectCreate, ProjectOut
from app.services.file_service import ensure_workspace, delete_workspace_dir

router = APIRouter(prefix="/api/projects", tags=["projects"])


def _session(request: Request) -> str:
    return getattr(request.state, "session_key", "default")


@router.post("", response_model=ProjectOut)
async def create_project(data: ProjectCreate, request: Request, db: AsyncSession = Depends(get_db)):
    try:
        pid = str(uuid.uuid4())
        wspath = ensure_workspace(pid)
        project = Project(id=pid, name=data.name, workspace_dir=wspath, session_key=_session(request))
        db.add(project)
        await db.commit()
        await db.refresh(project)
        return project
    except Exception as e:
        traceback.print_exc()
        await db.rollback()
        raise HTTPException(500, f"创建失败: {e}")


@router.get("", response_model=list[ProjectOut])
async def list_projects(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        sk = _session(request)
        result = await db.execute(
            select(Project).where(Project.session_key == sk).order_by(Project.updated_at.desc())
        )
        return list(result.scalars().all())
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, f"获取失败: {e}")


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(404, "Project not found")
    return project


@router.delete("/{project_id}")
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(404, "Project not found")
    delete_workspace_dir(project_id)
    await db.delete(project)
    await db.commit()
    return {"ok": True}


@router.get("/{project_id}/files", response_model=list[dict])
async def list_project_files(project_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(NoteFile).where(NoteFile.project_id == project_id).order_by(NoteFile.sort_order)
    )
    files = list(result.scalars().all())
    out = []
    for f in files:
        result2 = await db.execute(select(NoteEntry).where(NoteEntry.note_file_id == f.id))
        entries = list(result2.scalars().all())
        out.append({
            "id": f.id, "project_id": f.project_id, "filename": f.filename,
            "filepath": f.filepath, "keywords": f.keywords, "summary": f.summary,
            "color_tag": f.color_tag, "created_by_ai": f.created_by_ai,
            "sort_order": f.sort_order,
            "created_at": f.created_at.isoformat() if f.created_at else None,
            "updated_at": f.updated_at.isoformat() if f.updated_at else None,
            "entry_count": len(entries),
        })
    return out


@router.get("/{project_id}/files/{file_id}/entries")
async def list_file_entries(project_id: str, file_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(NoteEntry).where(NoteEntry.note_file_id == file_id).order_by(NoteEntry.sort_order)
    )
    entries = list(result.scalars().all())
    return [
        {
            "id": e.id, "note_file_id": e.note_file_id, "content": e.content,
            "highlighted_content": e.highlighted_content, "importance": e.importance,
            "color": e.color, "source_note": e.source_note, "sort_order": e.sort_order,
            "similarity_score": e.similarity_score, "linked_entry_id": e.linked_entry_id,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in entries
    ]
