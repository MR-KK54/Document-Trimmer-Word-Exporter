@echo off
setlocal enabledelayedexpansion
title Installing Document Trimmer ^& Exporter Pro...

echo ========================================================
echo   Document Trimmer ^& Exporter Pro - Desktop Installer
echo ========================================================
echo.

set "APP_DIR=%~dp0"
set "APP_DIR=%APP_DIR:~0,-1%"

rem Check Python Installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.10 or newer and check "Add Python to PATH".
    pause
    exit /b 1
)

echo [1/4] Setting up Python virtual environment...
if not exist "%APP_DIR%\.venv" (
    python -m venv "%APP_DIR%\.venv"
)

echo [2/4] Installing application dependencies and initializing database...
"%APP_DIR%\.venv\Scripts\python.exe" -m pip install --upgrade pip >nul 2>&1
"%APP_DIR%\.venv\Scripts\pip.exe" install -r "%APP_DIR%\requirements.txt"
"%APP_DIR%\.venv\Scripts\python.exe" -c "import db; print('[SUCCESS] Local SQLite Database Initialized!')"

echo [3/4] Creating Desktop Shortcut with Custom Logo Icon...
"%APP_DIR%\.venv\Scripts\python.exe" "%APP_DIR%\create_desktop_shortcut.py"

echo [4/4] Installation Complete!
echo.
echo Desktop Shortcut "Document Trimmer Pro" created successfully!
echo Launching Application...

if exist "%APP_DIR%\Document_Trimmer_Pro\Document_Trimmer_Pro.exe" (
    start "" "%APP_DIR%\Document_Trimmer_Pro\Document_Trimmer_Pro.exe"
) else if exist "%APP_DIR%\dist\Document_Trimmer_Pro\Document_Trimmer_Pro.exe" (
    start "" "%APP_DIR%\dist\Document_Trimmer_Pro\Document_Trimmer_Pro.exe"
) else (
    start "" "%APP_DIR%\.venv\Scripts\pythonw.exe" "%APP_DIR%\launch_app.py"
)

exit /b 0
