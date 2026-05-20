import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.config import settings as app_settings
from app.database import init_db
from app.routers import project, classify, export, rule, settings, stream


FRONTEND_DIST = Path(__file__).parent.parent.parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(os.path.join(app_settings.data_dir, "workspaces"), exist_ok=True)
    await init_db()
    yield


app = FastAPI(title="Note Organizer", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware: extract session_id and api_key from headers
@app.middleware("http")
async def extract_session(request: Request, call_next):
    # Session key for data isolation (per-browser)
    session = request.headers.get("X-Session-ID", "default")
    request.state.session_key = session
    # API key from browser (overrides server setting)
    api_key = request.headers.get("X-API-Key", "")
    request.state.user_api_key = api_key
    response = await call_next(request)
    return response


app.include_router(project.router)
app.include_router(classify.router)
app.include_router(export.router)
app.include_router(rule.router)
app.include_router(settings.router)
app.include_router(stream.router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


# Serve built frontend
if FRONTEND_DIST.exists() and (FRONTEND_DIST / "index.html").exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str = ""):
        file_path = FRONTEND_DIST / full_path
        if full_path and file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIST / "index.html")
