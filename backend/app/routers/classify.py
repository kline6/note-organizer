import os
import traceback
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.project import Project
from app.models.note import NoteFile, NoteEntry
from app.models.snapshot import Snapshot
from app.schemas.rule import ClassifyRequest
from app.schemas.note import EntryMoveRequest, EntryMergeDecision
from app.services import file_service, classification_service
from app.services.ai_service import request_api_key

router = APIRouter(prefix="/api/classify", tags=["classify"])


def _set_api_key(request: Request):
    key = getattr(request.state, "user_api_key", "")
    if key:
        request_api_key.set(key)


def _err(e: Exception, msg: str = "") -> HTTPException:
    traceback.print_exc()
    return HTTPException(500, f"{msg}: {e}" if msg else str(e))


@router.post("/upload-summary")
async def upload_summary(
    project_id: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    try:
        if request: _set_api_key(request)
        result = await db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()
        if not project:
            raise HTTPException(404, "项目不存在")
        if not project.workspace_dir:
            raise HTTPException(500, "项目工作区未初始化")

        workspace = project.workspace_dir or os.path.join(file_service.ensure_workspace(project_id))
        project.workspace_dir = workspace
        os.makedirs(workspace, exist_ok=True)

        tmp_path = os.path.join(workspace, f"_tmp_{file.filename}")
        with open(tmp_path, "wb") as f:
            f.write(await file.read())

        final_path = file_service.copy_uploaded_file(tmp_path, workspace, file.filename)
        os.remove(tmp_path)

        text = file_service.read_text_file(final_path)
        results = await classification_service.run_classification(db, project_id, text, workspace)
        await db.commit()
        return {"ok": True, "results": results, "source_file": os.path.basename(final_path)}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise _err(e, "分类失败")


@router.post("/classify-text")
async def classify_text(data: ClassifyRequest, db: AsyncSession = Depends(get_db), request: Request = None):
    try:
        if request: _set_api_key(request)
        result = await db.execute(select(Project).where(Project.id == data.project_id))
        project = result.scalar_one_or_none()
        if not project:
            raise HTTPException(404, "项目不存在")
        results = await classification_service.run_classification(db, data.project_id, data.summary_text, project.workspace_dir)
        return {"ok": True, "results": results}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise _err(e, "文本分类失败")


@router.post("/upload-existing")
async def upload_existing_files(
    project_id: str = Form(...),
    files: list[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()
        if not project:
            raise HTTPException(404, "项目不存在")

        workspace = project.workspace_dir
        os.makedirs(workspace, exist_ok=True)

        added = []
        for file in files:
            tmp_path = os.path.join(workspace, f"_tmp_{file.filename}")
            with open(tmp_path, "wb") as f:
                f.write(await file.read())
            final_path = file_service.copy_uploaded_file(tmp_path, workspace, file.filename)
            os.remove(tmp_path)

            content = file_service.read_text_file(final_path)
            filename = os.path.basename(final_path)

            result2 = await db.execute(
                select(NoteFile).where(NoteFile.project_id == project_id, NoteFile.filename == filename)
            )
            if result2.scalar_one_or_none():
                continue

            nf = NoteFile(project_id=project_id, filename=filename, filepath=final_path)
            db.add(nf)
            await db.flush()

            paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
            for idx, para in enumerate(paragraphs):
                db.add(NoteEntry(note_file_id=nf.id, content=para, sort_order=idx))

            added.append({"id": nf.id, "filename": filename, "entry_count": len(paragraphs)})

        await db.commit()
        return {"ok": True, "added": added}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise _err(e, "导入文件失败")


@router.post("/move-entry")
async def move_entry(data: EntryMoveRequest, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(NoteEntry).where(NoteEntry.id == data.entry_id))
        entry = result.scalar_one_or_none()
        if not entry:
            raise HTTPException(404, "条目不存在")
        entry.note_file_id = data.target_file_id
        await db.commit()
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise _err(e)


@router.post("/merge-decision")
async def handle_merge_decision(data: EntryMergeDecision, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(NoteEntry).where(NoteEntry.id == data.entry_id))
        entry = result.scalar_one_or_none()
        if not entry:
            raise HTTPException(404, "条目不存在")
        if data.action == "skip":
            await db.delete(entry)
        elif data.action == "merge":
            entry.similarity_score = 0.9
        await db.commit()
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise _err(e)


@router.delete("/entries/{entry_id}")
async def delete_entry(entry_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(NoteEntry).where(NoteEntry.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(404, "条目不存在")
    await db.delete(entry)
    await db.commit()
    return {"ok": True}


@router.delete("/files/{file_id}")
async def delete_file(file_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(NoteFile).where(NoteFile.id == file_id))
    nf = result.scalar_one_or_none()
    if not nf:
        raise HTTPException(404, "文件不存在")
    if nf.filepath and os.path.exists(nf.filepath):
        os.remove(nf.filepath)
    await db.delete(nf)
    await db.commit()
    return {"ok": True}


@router.post("/snapshot")
async def create_snapshot(project_id: str = Form(...), db: AsyncSession = Depends(get_db)):
    try:
        snap = await classification_service.save_snapshot(db, project_id, "手动快照")
        await db.commit()
        return {"ok": True, "snapshot_id": snap.id}
    except Exception as e:
        await db.rollback()
        raise _err(e)


@router.get("/{project_id}/snapshots")
async def list_snapshots(project_id: str, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(
            select(Snapshot).where(Snapshot.project_id == project_id).order_by(Snapshot.created_at.desc())
        )
        snaps = list(result.scalars().all())
        return [{"id": s.id, "description": s.description, "created_at": s.created_at.isoformat() if s.created_at else None} for s in snaps]
    except Exception as e:
        raise _err(e)


@router.post("/{project_id}/restore/{snapshot_id}")
async def restore_snapshot(project_id: str, snapshot_id: str, db: AsyncSession = Depends(get_db)):
    try:
        await classification_service.restore_snapshot(db, project_id, snapshot_id)
        return {"ok": True}
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        await db.rollback()
        raise _err(e)
