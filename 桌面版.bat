@echo off
cd /d "%~dp0"
setlocal enabledelayedexpansion

echo.
echo ================================================
echo   NoteOrganizer Desktop (Native Window)
echo ================================================
echo.

REM Find Python
set PY=
for %%d in (
    "%LOCALAPPDATA%\Programs\Python\Python312"
    "%LOCALAPPDATA%\Programs\Python\Python313"
    "C:\Python312" "C:\Python313"
) do (
    if exist "%%d\python.exe" (
        "%%d\python.exe" --version >nul 2>&1
        if not errorlevel 1 set PY=%%d\python.exe && goto pyok
    )
)
echo [ERROR] Python 3.12+ required
pause & exit /b 1

:pyok
echo [OK] Python: %PY%

REM Install electron deps
echo.
echo [1/3] Checking Electron dependencies...
cd /d "%~dp0electron"
if not exist "node_modules\" (
    echo Installing...
    call npm install
)
echo [OK] Done

REM Build frontend
echo.
echo [2/3] Building frontend...
cd /d "%~dp0frontend"
if not exist "node_modules\" (
    call npm install
)
call npm run build
if not exist "dist\index.html" (
    echo [FAIL] Frontend build failed
    pause & exit /b 1
)
echo [OK] Done

REM Start Electron
echo.
echo [3/3] Starting desktop app...
echo (A native window will open - NOT your browser)
cd /d "%~dp0electron"
call npx electron .
