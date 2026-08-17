@echo off
TITLE Document Trimmer Pro - Desktop Application Installer
COLOR 0A
echo =========================================================================
echo               DOCUMENT TRIMMER PRO - DESKTOP APP INSTALLER
echo =========================================================================
echo.
echo [1/3] Installing Python dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pywin32
echo.
echo [2/3] Creating Desktop and Start Menu Shortcuts...
python -c "import os, sys; from win32com.client import Dispatch; desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop'); start_menu = os.path.join(os.environ['APPDATA'], 'Microsoft', 'Windows', 'Start Menu', 'Programs'); proj_dir = r'%~dp0'.rstrip('\\'); py_exe = sys.executable; launch_py = os.path.join(proj_dir, 'launch_app.py'); icon_path = os.path.join(proj_dir, 'app_icon.ico'); shell = Dispatch('WScript.Shell'); s_desk = shell.CreateShortCut(os.path.join(desktop, 'Document Trimmer Pro.lnk')); s_desk.TargetPath = py_exe; s_desk.Arguments = f'\"{launch_py}\"'; s_desk.WorkingDirectory = proj_dir; s_desk.IconLocation = icon_path; s_desk.Save(); s_start = shell.CreateShortCut(os.path.join(start_menu, 'Document Trimmer Pro.lnk')); s_start.TargetPath = py_exe; s_start.Arguments = f'\"{launch_py}\"'; s_start.WorkingDirectory = proj_dir; s_start.IconLocation = icon_path; s_start.Save(); print('Successfully created Desktop and Start Menu shortcuts!')"
echo.
echo [3/3] Launching Document Trimmer Pro Desktop Application...
start "" python "%~dp0launch_app.py"
echo.
echo =========================================================================
echo Installation complete! Document Trimmer Pro Desktop App is now live.
echo Shortcut created on your Desktop!
echo =========================================================================
pause
