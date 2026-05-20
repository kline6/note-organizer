@echo off
cd /d "%~dp0"
setlocal enabledelayedexpansion

echo.
echo ================================================
echo   NoteOrganizer EXE Builder
echo ================================================
echo.

REM --- Find real Python (skip MS Store stub) ---
set PY=
for %%d in (
    "%LOCALAPPDATA%\Programs\Python\Python312"
    "%LOCALAPPDATA%\Programs\Python\Python313"
    "%LOCALAPPDATA%\Programs\Python\Python311"
    "%LOCALAPPDATA%\Programs\Python\Python310"
    "C:\Python312" "C:\Python313" "C:\Python311"
) do (
    if exist "%%d\python.exe" (
        "%%d\python.exe" --version >nul 2>&1
        if not errorlevel 1 set PY=%%d\python.exe && goto pyok
    )
)
REM Fallback: try PATH
for %%p in (python3 python) do (
    %%p --version >nul 2>&1
    if not errorlevel 1 (
        for /f "delims=" %%i in ('where %%p 2^>nul') do set PY=%%i && goto pyok
    )
)
echo [ERROR] Python not found. Install Python 3.12 from python.org
pause & exit /b 1

:pyok
echo [OK] Python: %PY%
"%PY%" --version
echo.

REM --- Install PyInstaller ---
echo [1/3] Installing PyInstaller...
"%PY%" -m pip install pyinstaller -q
if errorlevel 1 (
    echo [FAIL] PyInstaller install failed
    pause & exit /b 1
)
echo [OK] Done

REM --- Build frontend ---
echo.
echo [2/3] Building frontend...
cd /d "%~dp0frontend"
if not exist "node_modules\" (
    echo Installing npm packages...
    call npm install
)
call npm run build
if not exist "dist\index.html" (
    echo [FAIL] Frontend build failed
    cd /d "%~dp0"
    pause & exit /b 1
)
echo [OK] Done

REM --- Clean old build ---
echo.
echo [3/4] Cleaning old build...
cd /d "%~dp0"
if exist "dist\NoteOrganizer.exe" del /f "dist\NoteOrganizer.exe"
if exist "build\" rmdir /s /q "build"
if exist "dist\" rmdir /s /q "dist"
echo [OK] Cleaned

REM --- Run PyInstaller ---
echo.
echo [4/4] Building EXE (3-5 min)...
cd /d "%~dp0"
"%PY%" -m PyInstaller --onefile --console --clean --noconfirm --name=NoteOrganizer --add-data "backend;backend" --add-data "frontend/dist;frontend/dist" --hidden-import=fastapi --hidden-import=uvicorn --hidden-import=sqlalchemy --hidden-import=aiosqlite --hidden-import=openai --hidden-import=pydantic --hidden-import=pydantic_settings --hidden-import=fpdf --hidden-import=fpdf2 --hidden-import=httpx --hidden-import=python_multipart --hidden-import=docx --hidden-import=markdown --hidden-import=bs4 --hidden-import=jieba --hidden-import=anyio --hidden-import=starlette --hidden-import=click --hidden-import=h11 --hidden-import=websockets --hidden-import=uvloop --collect-all=uvicorn --collect-all=fastapi --collect-all=starlette --exclude-module=weasyprint --exclude-module=reportlab _exe_entry.py

if exist "dist\NoteOrganizer.exe" (
    echo.
    echo ================================================
    echo   SUCCESS!
    echo   EXE: dist\NoteOrganizer.exe
    echo   Copy it anywhere - no Python needed.
    echo ================================================
) else (
    echo.
    echo [FAIL] EXE not found. Check errors above.
)
echo.
pause
