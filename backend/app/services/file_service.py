import os
import shutil
import uuid
from pathlib import Path
from app.config import settings


def ensure_workspace(project_id: str) -> str:
    workspace = Path(settings.data_dir) / "workspaces" / project_id
    workspace.mkdir(parents=True, exist_ok=True)
    return str(workspace)


def copy_uploaded_file(upload_path: str, workspace: str, filename: str) -> str:
    """Copy uploaded file to workspace, auto-rename if conflict."""
    base, ext = os.path.splitext(filename)
    dest = os.path.join(workspace, filename)
    counter = 1
    while os.path.exists(dest):
        dest = os.path.join(workspace, f"{base}_{counter}{ext}")
        counter += 1
    shutil.copy2(upload_path, dest)
    return dest


def read_text_file(filepath: str) -> str:
    encodings = ["utf-8", "gbk", "gb2312", "latin-1"]
    for enc in encodings:
        try:
            with open(filepath, "r", encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Cannot decode file: {filepath}")


def write_text_file(filepath: str, content: str) -> None:
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


def read_all_note_files(workspace: str) -> list[dict]:
    """Read all .txt/.md files from workspace and return their info."""
    files = []
    if not os.path.exists(workspace):
        return files
    for fname in sorted(os.listdir(workspace)):
        if fname.endswith((".txt", ".md", ".markdown")):
            fpath = os.path.join(workspace, fname)
            files.append({
                "filename": fname,
                "filepath": fpath,
                "size": os.path.getsize(fpath),
            })
    return files


def create_empty_note_file(workspace: str, filename: str) -> str:
    """Create a new empty note file."""
    base, ext = os.path.splitext(filename)
    if not ext:
        ext = ".txt"
        filename = f"{base}.txt"
    fpath = os.path.join(workspace, filename)
    counter = 1
    while os.path.exists(fpath):
        fpath = os.path.join(workspace, f"{base}_{counter}{ext}")
        counter += 1
    write_text_file(fpath, "")
    return fpath


def delete_workspace_dir(project_id: str) -> None:
    workspace = Path(settings.data_dir) / "workspaces" / project_id
    if workspace.exists():
        shutil.rmtree(workspace)
