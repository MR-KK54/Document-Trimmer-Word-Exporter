@echo off
TITLE Document Trimmer Pro - Uninstaller
echo =========================================================================
echo               Document Trimmer Pro - Complete Uninstaller
echo =========================================================================
echo.

echo [1/3] Terminating any running Document Trimmer processes...
taskkill /F /IM Document_Trimmer_Pro.exe 2>NUL
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Document Trimmer*" 2>NUL

echo [2/3] Removing Windows Shortcuts...
set DESKTOP_LINK="%USERPROFILE%\Desktop\Document Trimmer Pro.lnk"
set START_LINK="%APPDATA%\Microsoft\Windows\Start Menu\Programs\Document Trimmer Pro.lnk"

if exist %DESKTOP_LINK% del /f /q %DESKTOP_LINK%
if exist %START_LINK% del /f /q %START_LINK%

echo [3/3] Uninstallation completed successfully!
echo =========================================================================
echo Document Trimmer Pro shortcuts and running services have been removed.
echo.
pause
