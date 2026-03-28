@echo off
cd /d "%~dp0"

REM Try pythonw first (runs silently, no terminal window).
REM Falls back to python if pythonw is not found.
where pythonw >nul 2>&1
if %errorlevel% == 0 (
    start "" pythonw app.py
) else (
    python app.py
)
