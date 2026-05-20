"""
SSE streaming endpoint for real-time classification progress.
"""
import json
import os
import traceback
from fastapi import APIRouter, Request, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db, async_session
from app.models.project import Project
from app.models.note import NoteFile, NoteEntry
from app.models.rule import ClassificationRule, HighlightRule
from app.services import ai_service, file_service
from app.services.ai_service import request_api_key

router = APIRouter(prefix="/api/stream", tags=["stream"])


async def _classify_stream(project_id: str, summary_text: str, api_key: str):
    """Generator that yields SSE events as classification progresses."""
    try:
        if api_key:
            request_api_key.set(api_key)

        async with async_session() as db:
            # Load project
            result = await db.execute(select(Project).where(Project.id == project_id))
            project = result.scalar_one_or_none()
            if not project:
                yield f"data: {json.dumps({'type': 'error', 'msg': 'Project not found'}, ensure_ascii=False)}\n\n"
                return

            workspace = project.workspace_dir or os.path.join(file_service.ensure_workspace(project_id))
            os.makedirs(workspace, exist_ok=True)

            # Load existing files & rules
            result = await db.execute(select(NoteFile).where(NoteFile.project_id == project_id))
            existing_files = list(result.scalars().all())
            result = await db.execute(select(ClassificationRule).where(ClassificationRule.project_id == project_id))
            rules = list(result.scalars().all())
            result = await db.execute(select(HighlightRule).where(HighlightRule.project_id == project_id))
            highlight_rules = list(result.scalars().all())

            existing_files_ctx = []
            for f in existing_files:
                r2 = await db.execute(select(NoteEntry).where(NoteEntry.note_file_id == f.id))
                entries = list(r2.scalars().all())
                existing_files_ctx.append({
                    "id": f.id, "filename": f.filename, "keywords": f.keywords,
                    "summary": f.summary,
                    "entries": [{"id": e.id, "content": e.content} for e in entries],
                })

            rules_ctx = [{"pattern": r.pattern, "target_file": r.target_file} for r in rules]
            filename_to_id = {f.filename: f.id for f in existing_files}

            # Step 1: Split text into entries
            yield f"data: {json.dumps({'type': 'status', 'msg': 'AI 正在分析拆分...'}, ensure_ascii=False)}\n\n"

            entries = await ai_service.split_summary_into_entries(summary_text)
            total = len(entries)

            if total == 0:
                yield f"data: {json.dumps({'type': 'error', 'msg': '未能从文本中提取条目'}, ensure_ascii=False)}\n\n"
                return

            yield f"data: {json.dumps({'type': 'status', 'msg': f'共 {total} 条，逐条分类中...'}, ensure_ascii=False)}\n\n"

            created_files = []
            assigned_count = 0
            new_count = 0

            for idx, entry in enumerate(entries):
                entry_content = entry.get("content", "")
                if not entry_content:
                    continue

                yield f"data: {json.dumps({'type': 'status', 'msg': f'正在分析 {idx+1}/{total}...'}, ensure_ascii=False)}\n\n"

                classification = await ai_service.classify_entry_to_file(entry, existing_files_ctx, rules_ctx)

                target_file_id = None
                target_filename = None
                is_new_file = False

                if classification.get("action") == "assign":
                    target_filename = classification.get("target_file", "")
                    normalized = target_filename.strip().removesuffix(".txt").removesuffix(".md") + ".txt"
                    target_file_id = filename_to_id.get(target_filename) or filename_to_id.get(normalized)
                    if not target_file_id:
                        for f in existing_files:
                            fn = f.filename.strip().removesuffix(".txt").removesuffix(".md") + ".txt"
                            if fn == normalized:
                                target_file_id = f.id
                                break

                if not target_file_id:
                    new_filename = classification.get("new_filename", f"新建笔记_{idx + 1}.txt")
                    new_filepath = file_service.create_empty_note_file(workspace, new_filename)
                    new_filename = new_filepath.split("/")[-1].split("\\")[-1]
                    new_file = NoteFile(
                        project_id=project_id, filename=new_filename, filepath=new_filepath,
                        keywords=",".join(classification.get("keywords", [])), created_by_ai=True,
                    )
                    db.add(new_file)
                    await db.flush()
                    target_file_id = new_file.id
                    target_filename = new_filename
                    is_new_file = True
                    filename_to_id[new_filename] = new_file.id
                    existing_files_ctx.append({
                        "id": new_file.id, "filename": new_filename,
                        "keywords": new_file.keywords, "summary": "", "entries": [],
                    })
                    created_files.append({"id": new_file.id, "filename": new_filename, "entry_count": 0})
                    new_count += 1
                else:
                    assigned_count += 1

                new_entry = NoteEntry(
                    note_file_id=target_file_id,
                    content=entry_content,
                    highlighted_content=entry_content,
                    importance=entry.get("importance", "medium"),
                    color=entry.get("color", "blue"),
                    sort_order=idx,
                )
                db.add(new_entry)
                await db.flush()

                # Update file entry count
                for cf in created_files:
                    if cf["id"] == target_file_id:
                        cf["entry_count"] += 1

                await db.commit()

                # Send SSE event for this entry
                yield f"data: {json.dumps({'type': 'entry', 'idx': idx + 1, 'total': total, 'content': entry_content[:80], 'file': target_filename, 'is_new': is_new_file, 'entry_id': new_entry.id, 'file_id': target_file_id, 'assigned': assigned_count, 'new': new_count}, ensure_ascii=False)}\n\n"

            yield f"data: {json.dumps({'type': 'done', 'total': total, 'assigned': assigned_count, 'new': new_count, 'files': created_files}, ensure_ascii=False)}\n\n"

    except Exception as e:
        traceback.print_exc()
        yield f"data: {json.dumps({'type': 'error', 'msg': str(e)}, ensure_ascii=False)}\n\n"


@router.post("/classify")
async def stream_classify(request: Request):
    """SSE streaming classification endpoint."""
    try:
        body = await request.json()
    except Exception:
        body = {}

    project_id = body.get("project_id", "")
    summary_text = body.get("summary_text", "")
    api_key = request.headers.get("X-API-Key", "")

    if not project_id or not summary_text:
        return StreamingResponse(
            iter([f"data: {json.dumps({'type': 'error', 'msg': 'Missing project_id or text'}, ensure_ascii=False)}\n\n"]),
            media_type="text/event-stream",
        )

    return StreamingResponse(
        _classify_stream(project_id, summary_text, api_key),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
