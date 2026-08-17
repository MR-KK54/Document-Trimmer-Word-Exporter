import os
import sqlite3
import hashlib
import uuid
import json
import shutil
import time
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_DIR = os.path.join(BASE_DIR, "storage")
DB_PATH = os.path.join(STORAGE_DIR, "database.db")
BACKUP_DIR = os.path.join(STORAGE_DIR, "backups")
UPLOADS_DIR = os.path.join(STORAGE_DIR, "uploads")
EXPORTS_DIR = os.path.join(STORAGE_DIR, "exports")

# Ensure required local storage directories exist
for folder in [STORAGE_DIR, BACKUP_DIR, UPLOADS_DIR, EXPORTS_DIR]:
    os.makedirs(folder, exist_ok=True)

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            role TEXT DEFAULT 'admin',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Sessions Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    # Jobs Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            file_type TEXT NOT NULL,
            range_spec TEXT NOT NULL,
            status TEXT NOT NULL,
            output_files_json TEXT,
            total_pages INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Activity Logs Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            level TEXT NOT NULL,
            message TEXT NOT NULL,
            ip TEXT DEFAULT '127.0.0.1'
        )
    """)

    # Backups Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS backups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            filepath TEXT NOT NULL,
            size_bytes INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Settings Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    # Insert default settings if not exists
    default_settings = {
        "auto_zip": "true",
        "lan_access": "false",
        "max_job_history": "100",
        "auto_backup_enabled": "true"
    }
    for k, v in default_settings.items():
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))

    # Create default admin user if no users exist
    cursor.execute("SELECT COUNT(*) as cnt FROM users")
    if cursor.fetchone()["cnt"] == 0:
        create_user("admin", "admin123")

    conn.commit()
    conn.close()

# Password Hashing Functions
def _hash_password(password, salt=None):
    if not salt:
        salt = uuid.uuid4().hex
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000).hex()
    return hashed, salt

def create_user(username, password, role="admin"):
    conn = get_connection()
    cursor = conn.cursor()
    pwd_hash, salt = _hash_password(password)
    try:
        cursor.execute("INSERT INTO users (username, password_hash, salt, role) VALUES (?, ?, ?, ?)",
                       (username, pwd_hash, salt, role))
        conn.commit()
        log_activity("INFO", f"User '{username}' created successfully.")
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def verify_user(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    if not user:
        return None
    pwd_hash, _ = _hash_password(password, user["salt"])
    if pwd_hash == user["password_hash"]:
        return dict(user)
    return None

# Session Management
def create_session(user_id, duration_hours=24):
    conn = get_connection()
    cursor = conn.cursor()
    token = uuid.uuid4().hex
    expires_at = int(time.time()) + (duration_hours * 3600)
    cursor.execute("INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)",
                   (token, user_id, expires_at))
    conn.commit()
    conn.close()
    return token

def validate_session(token):
    if not token:
        return None
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.*, u.username, u.role FROM sessions s
        JOIN users u ON s.user_id = u.id
        WHERE s.token = ? AND s.expires_at > ?
    """, (token, int(time.time())))
    session = cursor.fetchone()
    conn.close()
    return dict(session) if session else None

def delete_session(token):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sessions WHERE token = ?", (token,))
    conn.commit()
    conn.close()

# Activity Logging
def log_activity(level, message, ip="127.0.0.1"):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO activity_logs (level, message, ip) VALUES (?, ?, ?)",
                       (level, message, ip))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[DB Log Error] {e}")

def get_activity_logs(limit=50):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM activity_logs ORDER BY id DESC LIMIT ?", (limit,))
    logs = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return logs

# Jobs Management
def save_job(job_id, filename, file_type, range_spec, status="processing", output_files=None, total_pages=0):
    conn = get_connection()
    cursor = conn.cursor()
    output_json = json.dumps(output_files) if output_files else None
    cursor.execute("""
        INSERT OR REPLACE INTO jobs (job_id, filename, file_type, range_spec, status, output_files_json, total_pages)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (job_id, filename, file_type, range_spec, status, output_json, total_pages))
    conn.commit()
    conn.close()
    log_activity("INFO", f"Job '{job_id}' ({filename}) saved with status: {status}")

def get_job_history(limit=50):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,))
    jobs = []
    for row in cursor.fetchall():
        item = dict(row)
        if item["output_files_json"]:
            try:
                item["output_files"] = json.loads(item["output_files_json"])
            except Exception:
                item["output_files"] = []
        else:
            item["output_files"] = []
        jobs.append(item)
    conn.close()
    return jobs

# Backup & Restore Management
def create_backup():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"db_backup_{timestamp}.db"
    backup_filepath = os.path.join(BACKUP_DIR, backup_filename)

    shutil.copy2(DB_PATH, backup_filepath)
    size_bytes = os.path.getsize(backup_filepath)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO backups (filename, filepath, size_bytes) VALUES (?, ?, ?)",
                   (backup_filename, backup_filepath, size_bytes))
    conn.commit()
    conn.close()

    log_activity("INFO", f"Local Database Backup created: '{backup_filename}' ({size_bytes} bytes)")
    return {"filename": backup_filename, "filepath": backup_filepath, "size_bytes": size_bytes}

def get_backups():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM backups ORDER BY id DESC")
    backups = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return backups

def restore_backup(backup_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM backups WHERE id = ?", (backup_id,))
    backup = cursor.fetchone()
    conn.close()

    if not backup or not os.path.exists(backup["filepath"]):
        return False, "Backup file not found"

    shutil.copy2(backup["filepath"], DB_PATH)
    log_activity("WARNING", f"Database restored from backup: '{backup['filename']}'")
    return True, f"Successfully restored database from {backup['filename']}"

# Settings Management
def get_settings():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM settings")
    settings = {r["key"]: r["value"] for r in cursor.fetchall()}
    conn.close()
    return settings

def update_setting(key, value):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()
    log_activity("INFO", f"Setting '{key}' updated to '{value}'")

# Initialize database on module import
init_db()
