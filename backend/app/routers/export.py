import os
import traceback
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.export_service import export_all_files, export_single_file

router = APIRouter(prefix="/api/export", tags=["export"])


@router.post("/all/{project_id}")
async def export_project(project_id: str, fmt: str = "md", db: AsyncSession = Depends(get_db)):
    if fmt not in ("md", "html", "txt", "docx", "pdf"):
        raise HTTPException(400, f"不支持的格式: {fmt}")

    try:
        output_dir = await export_all_files(db, project_id, fmt)
    except ValueError as e:
        raise HTTPException(404, str(e))
    except RuntimeError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, f"导出失败: {e}")

    media_map = {
        "md": "text/markdown", "html": "text/html", "txt": "text/plain",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "pdf": "application/pdf",
    }

    if fmt in ("html", "docx", "pdf"):
        output_file = os.path.join(output_dir, f"export.{fmt}")
        if not os.path.exists(output_file):
            raise HTTPException(500, "导出文件未生成")
        return FileResponse(output_file, media_type=media_map.get(fmt, "application/octet-stream"),
                             filename=f"export.{fmt}")

    # md/txt: zip all individual files
    import zipfile
    zip_path = output_dir + ".zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        for root, dirs, files in os.walk(output_dir):
            for fn in files:
                zf.write(os.path.join(root, fn), fn)
    return FileResponse(zip_path, media_type="application/zip", filename=f"export_{project_id}.zip")


@router.post("/file/{file_id}")
async def export_single(file_id: str, fmt: str = "md", db: AsyncSession = Depends(get_db)):
    if fmt not in ("md", "html", "txt", "docx", "pdf"):
        raise HTTPException(400, f"不支持的格式: {fmt}")

    try:
        output_path = await export_single_file(db, file_id, fmt)
    except ValueError as e:
        raise HTTPException(404, str(e))
    except RuntimeError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, f"导出失败: {e}")

    media_map = {
        "md": "text/markdown", "html": "text/html", "txt": "text/plain",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "pdf": "application/pdf",
    }
    filename = os.path.basename(output_path)
    return FileResponse(output_path, media_type=media_map.get(fmt, "application/octet-stream"), filename=filename)
