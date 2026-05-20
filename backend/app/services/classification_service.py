import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.models.note import NoteFile, NoteEntry
from app.models.rule import ClassificationRule, HighlightRule
from app.models.snapshot import Snapshot
from app.services import ai_service, file_service


async def run_classification(
    db: AsyncSession,
    project_id: str,
    summary_text: str,
    workspace: str,
) -> dict:
    """Main classification pipeline. Returns summary of what was done."""

    # Skip auto-snapshot in classification flow (causes DB lock)
    # Snapshots can be created manually from the History tab

    # Load existing files and rules
    result = await db.execute(
        select(NoteFile).where(NoteFile.project_id == project_id)
    )
    existing_files = list(result.scalars().all())

    result = await db.execute(
        select(ClassificationRule)
        .where(ClassificationRule.project_id == project_id)
        .order_by(ClassificationRule.priority.desc())
    )
    rules = list(result.scalars().all())

    result = await db.execute(
        select(HighlightRule)
        .where(HighlightRule.project_id == project_id)
    )
    highlight_rules = list(result.scalars().all())

    # Step 1: Build context
    existing_files_ctx = []
    for f in existing_files:
        result2 = await db.execute(select(NoteEntry).where(NoteEntry.note_file_id == f.id))
        ef_entries = list(result2.scalars().all())
        existing_files_ctx.append({
            "id": f.id, "filename": f.filename, "keywords": f.keywords,
            "summary": f.summary,
            "entries": [{"id": e.id, "content": e.content} for e in ef_entries],
        })

    rules_ctx = [{"pattern": r.pattern, "target_file": r.target_file, "priority": r.priority} for r in rules]
    filename_to_id = {f.filename: f.id for f in existing_files}

    # Step 2: Split + classify in ONE AI call
    classifications = await ai_service.batch_classify(summary_text, existing_files_ctx, rules_ctx)

    results = {
        "total_entries": len(classifications),
        "assigned": [], "created_new": [], "similar_found": [],
        "cross_links": [], "skipped": 0,
    }

    for idx, classification in enumerate(classifications):
        entry_content = classification.get("content", "")
        if not entry_content:
            continue
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

        new_entry = NoteEntry(
            note_file_id=target_file_id,
            content=entry_content,
            highlighted_content=entry_content,
            importance=classification.get("importance", "medium"),
            color=classification.get("color", "blue"),
            sort_order=idx,
        )
        db.add(new_entry)
        await db.flush()

        entry_result = {
            "entry_id": new_entry.id,
            "content": entry_content[:100],
            "target_file": target_filename,
            "target_file_id": target_file_id,
            "is_new_file": is_new_file,
            "is_similar": False,
            "keywords": classification.get("keywords", []),
            "summary": classification.get("summary", ""),
        }
        if is_new_file:
            results["created_new"].append(entry_result)
        else:
            results["assigned"].append(entry_result)

    # Step 6: Generate keywords/summaries for new files (1 call per file)
    for cr in results["created_new"]:
        try:
            result3 = await db.execute(select(NoteEntry).where(NoteEntry.note_file_id == cr["target_file_id"]))
            file_entries = list(result3.scalars().all())
            if file_entries:
                kws_sum = await ai_service.generate_file_keywords_and_summary(
                    [{"content": e.content} for e in file_entries]
                )
                result4 = await db.execute(select(NoteFile).where(NoteFile.id == cr["target_file_id"]))
                nf = result4.scalar_one_or_none()
                if nf:
                    nf.keywords = ",".join(kws_sum.get("keywords", []))
                    nf.summary = kws_sum.get("summary", "")
        except Exception:
            pass  # Non-critical

    # Step 7: Cross-links skipped (adds 30s+ per entry, not critical)

    await db.commit()
    return results


async def save_snapshot(db: AsyncSession, project_id: str, description: str = "") -> Snapshot:
    """Save the current state of all notes as a JSON snapshot."""
    result = await db.execute(
        select(NoteFile).where(NoteFile.project_id == project_id)
    )
    files = list(result.scalars().all())

    state = {"files": []}
    for f in files:
        result2 = await db.execute(
            select(NoteEntry).where(NoteEntry.note_file_id == f.id).order_by(NoteEntry.sort_order)
        )
        entries = list(result2.scalars().all())
        state["files"].append({
            "id": f.id,
            "filename": f.filename,
            "filepath": f.filepath,
            "keywords": f.keywords,
            "summary": f.summary,
            "entries": [
                {
                    "id": e.id,
                    "content": e.content,
                    "highlighted_content": e.highlighted_content,
                    "importance": e.importance,
                    "color": e.color,
                    "sort_order": e.sort_order,
                    "note_file_id": e.note_file_id,
                }
                for e in entries
            ],
        })

    snapshot = Snapshot(
        project_id=project_id,
        description=description,
        state_json=json.dumps(state, ensure_ascii=False),
    )
    db.add(snapshot)
    await db.flush()
    return snapshot


async def restore_snapshot(db: AsyncSession, project_id: str, snapshot_id: str) -> None:
    """Restore project state from a snapshot."""
    result = await db.execute(
        select(Snapshot).where(Snapshot.id == snapshot_id, Snapshot.project_id == project_id)
    )
    snap = result.scalar_one_or_none()
    if not snap:
        raise ValueError("Snapshot not found")

    state = json.loads(snap.state_json)

    # Delete existing entries and files for this project
    await db.execute(delete(NoteEntry).where(
        NoteEntry.note_file_id.in_(
            select(NoteFile.id).where(NoteFile.project_id == project_id)
        )
    ))
    await db.execute(delete(NoteFile).where(NoteFile.project_id == project_id))
    await db.flush()

    # Restore from snapshot
    file_id_mapping = {}
    for fdata in state["files"]:
        new_file = NoteFile(
            id=fdata["id"],
            project_id=project_id,
            filename=fdata["filename"],
            filepath=fdata.get("filepath", ""),
            keywords=fdata.get("keywords"),
            summary=fdata.get("summary"),
        )
        db.add(new_file)
        await db.flush()
        file_id_mapping[fdata["id"]] = new_file.id

        for edata in fdata.get("entries", []):
            new_entry = NoteEntry(
                id=edata["id"],
                note_file_id=new_file.id,
                content=edata["content"],
                highlighted_content=edata.get("highlighted_content"),
                importance=edata.get("importance"),
                color=edata.get("color"),
                sort_order=edata.get("sort_order", 0),
            )
            db.add(new_entry)

    await db.commit()
