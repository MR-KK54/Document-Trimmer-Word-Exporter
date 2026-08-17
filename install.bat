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

echo [2/4] Installing application dependencies...
"%APP_DIR%\.venv\Scripts\python.exe" -m pip install --upgrade pip >nul 2>&1
"%APP_DIR%\.venv\Scripts\pip.exe" install -r "%APP_DIR%\requirements.txt"

echo [3/4] Creating Desktop Shortcut...
powershell -NoProfile -ExecutionPolicy Bypass -Command "^
    $WshShell = New-Object -ComObject WScript.Shell; ^
    $Shortcut = $WshShell.CreateShortcut([System.IO.Path]::Combine([Environment]::GetFolderPath('Desktop'), 'Document Trimmer Pro.lnk')); ^
    $Shortcut.TargetPath = '%APP_DIR%\.venv\Scripts\pythonw.exe'; ^
    $Shortcut.Arguments = '\"%APP_DIR%\launch_app.py\"'; ^
    $Shortcut.WorkingDirectory = '%APP_DIR%'; ^
    $Shortcut.Description = 'Document Trimmer & Word Exporter Pro Desktop App'; ^
    $Shortcut.Save(); ^
    $StartMenu = [System.IO.Path]::Combine([Environment]::GetFolderPath('StartMenu'), 'Programs', 'Document Trimmer Pro.lnk'); ^
    $Shortcut2 = $WshShell.CreateShortcut($StartMenu); ^
    $Shortcut2.TargetPath = '%APP_DIR%\.venv\Scripts\pythonw.exe'; ^
    $Shortcut2.Arguments = '\"%APP_DIR%\launch_app.py\"'; ^
    $Shortcut2.WorkingDirectory = '%APP_DIR%'; ^
    $Shortcut2.Description = 'Document Trimmer & Word Exporter Pro Desktop App'; ^
    $Shortcut2.Save();"

echo [4/4] Installation Complete!
echo.
echo Desktop Shortcut "Document Trimmer Pro" created successfully!
echo Launching Application...

start "" "%APP_DIR%\.venv\Scripts\pythonw.exe" "%APP_DIR%\launch_app.py"

exit /b 0
