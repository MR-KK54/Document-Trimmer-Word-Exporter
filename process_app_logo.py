import os
from PIL import Image

src_img = r"C:\Users\Hxtreme\.gemini\antigravity\brain\c377378a-dc19-40b1-acb5-a98613db1497\app_logo_1786954877896.jpg"
base_dir = os.path.dirname(os.path.abspath(__file__))
icons_dir = os.path.join(base_dir, "static", "icons")
os.makedirs(icons_dir, exist_ok=True)

img = Image.open(src_img).convert("RGBA")

# Save PNG icons
img.resize((512, 512), Image.Resampling.LANCZOS).save(os.path.join(icons_dir, "icon-512.png"))
img.resize((192, 192), Image.Resampling.LANCZOS).save(os.path.join(icons_dir, "icon-192.png"))
img.resize((64, 64), Image.Resampling.LANCZOS).save(os.path.join(base_dir, "static", "favicon.png"))

# Save ICO icons for Windows Desktop Shortcuts and PyInstaller EXE
ico_path = os.path.join(base_dir, "app_icon.ico")
favicon_ico = os.path.join(base_dir, "favicon.ico")

img.save(ico_path, format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
img.save(favicon_ico, format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])

print("[SUCCESS] Processed app logo into app_icon.ico and static icons!")
