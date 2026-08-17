import subprocess, os, sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
venv_python = os.path.join(BASE_DIR, ".venv", "Scripts", "python.exe")

cmd = [
    venv_python, "-m", "PyInstaller",
    "--noconfirm",
    "--onedir",
    "--windowed",
    "--name=Document_Trimmer_Pro",
    "--icon=app_icon.ico",
    "--add-data=index.html;.",
    "--add-data=manifest.json;.",
    "--add-data=sw.js;.",
    "--add-data=app_icon.ico;.",
    "--add-data=favicon.ico;.",
    "--add-data=static;static",
    "--add-data=engine;engine",
    "launch_app.py"
]

print("Running PyInstaller build:", " ".join(cmd))
res = subprocess.run(cmd, cwd=BASE_DIR)
if res.returncode == 0:
    print("[SUCCESS] Standalone Executable Package built in dist/Document_Trimmer_Pro/")
else:
    print("[ERROR] PyInstaller build failed with exit code:", res.returncode)
