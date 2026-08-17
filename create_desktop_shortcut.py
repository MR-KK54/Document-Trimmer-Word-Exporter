import os, sys, win32com.client

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
desktop = os.path.join(os.path.expanduser("~"), "Desktop")

# Prefer pre-compiled standalone EXE if present, else fallback to pythonw launcher
exe_path = os.path.join(BASE_DIR, "Document_Trimmer_Pro", "Document_Trimmer_Pro.exe")
if not os.path.exists(exe_path):
    exe_path = os.path.join(BASE_DIR, "dist", "Document_Trimmer_Pro", "Document_Trimmer_Pro.exe")
if not os.path.exists(exe_path):
    target_exe = os.path.join(BASE_DIR, ".venv", "Scripts", "pythonw.exe")
    target_script = os.path.join(BASE_DIR, "launch_app.py")
    args = f'"{target_script}"'
else:
    target_exe = exe_path
    args = ""

shell = win32com.client.Dispatch("WScript.Shell")

# Create Shortcut on User's Desktop
shortcut_path = os.path.join(desktop, "Document Trimmer Pro.lnk")
sc = shell.CreateShortcut(shortcut_path)
sc.TargetPath = target_exe
sc.Arguments = f'"{target_script}"'
sc.WorkingDirectory = BASE_DIR
sc.IconLocation = os.path.join(BASE_DIR, "app_icon.ico")
sc.Description = "Document Trimmer & Word Exporter Pro Desktop App"
sc.Save()

# Create Shortcut in Start Menu
start_menu = os.path.join(os.path.expanduser("~"), "AppData", "Roaming", "Microsoft", "Windows", "Start Menu", "Programs")
shortcut_path2 = os.path.join(start_menu, "Document Trimmer Pro.lnk")
sc2 = shell.CreateShortcut(shortcut_path2)
sc2.TargetPath = target_exe
sc2.Arguments = f'"{target_script}"'
sc2.WorkingDirectory = BASE_DIR
sc2.IconLocation = os.path.join(BASE_DIR, "app_icon.ico")
sc2.Description = "Document Trimmer & Word Exporter Pro Desktop App"
sc2.Save()

print(f"[SUCCESS] Desktop Shortcut created at: {shortcut_path}")
print(f"[SUCCESS] Start Menu Shortcut created at: {shortcut_path2}")
