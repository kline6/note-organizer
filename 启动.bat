@echo off
cd /d "%~dp0"
setlocal enabledelayedexpansion

set PY=

REM --- Method 1: system PATH ---
for %%p in (python3 python py) do (
    where %%p >nul 2>nul
    if not errorlevel 1 (
        for /f "delims=" %%i in ('where %%p 2^>nul') do (
            %%i --version >nul 2>nul
            if not errorlevel 1 set PY=%%i && goto run
        )
    )
)

REM --- Method 2: scan known install paths ---
for %%v in (313 312 311 310) do (
    for %%b in (
        "%LOCALAPPDATA%\Programs\Python\Python%%v\python.exe"
        "C:\Python%%v\python.exe"
        "%PROGRAMFILES%\Python%%v\python.exe"
        "%PROGRAMFILES(x86)%\Python%%v\python.exe"
    ) do (
        if exist %%b (
            %%b --version >nul 2>nul
            if not errorlevel 1 set PY=%%b && goto run
        )
    )
)

REM --- Method 3: py launcher ---
where py >nul 2>nul
if not errorlevel 1 (
    for /f "tokens=2 delims=: " %%v in ('py -3.12 --version 2^>nul') do set PY=py -3.12 && goto run
    for /f "tokens=2 delims=: " %%v in ('py -3.13 --version 2^>nul') do set PY=py -3.13 && goto run
    for /f "tokens=2 delims=: " %%v in ('py -3 --version 2^>nul') do set PY=py -3 && goto run
)

REM --- Not found ---
echo.
echo Python not found. Please install Python 3.10-3.13:
echo   https://www.python.org/downloads/
echo.
echo If already installed, run these two commands in CMD to check:
echo   dir "%LOCALAPPDATA%\Programs\Python" /b
echo   py --list
echo.
pause
exit /b 1

:run
echo.
echo Python found: %PY%
%PY% --version
echo.
%PY% start.py
pause
