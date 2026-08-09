"""Document format conversion.

On Windows, MS Word (COM) is the conversion engine - it produces byte-for-byte
Word-exact output. On Linux (Render), LibreOffice is used only as an optional
conversion helper; if it is unavailable, docx/docm outputs still work because
the trimming engine writes real Word packages directly.
"""

import os
import shutil
import subprocess
import tempfile
import threading

from . import word_com

_lock = threading.Lock()

_CANDIDATES = [
    "soffice",
    "libreoffice",
    "C:\\Program Files\\LibreOffice\\program\\soffice.exe",
    "C:\\Program Files (x86)\\LibreOffice\\program\\soffice.exe",
    "/usr/bin/soffice",
    "/usr/lib/libreoffice/program/soffice",
    "/opt/libreoffice/program/soffice",
    "/usr/local/bin/soffice",
]

_soffice_cache = None


def find_soffice():
    """Return the soffice binary path or None if LibreOffice is unavailable."""
    global _soffice_cache
    if _soffice_cache is not None:
        return _soffice_cache

    env = os.environ.get("SOFFICE_BIN")
    if env and shutil.which(env):
        _soffice_cache = env
        return _soffice_cache

    for c in _CANDIDATES:
        if os.path.sep in c:
            if os.path.exists(c):
                _soffice_cache = c
                return _soffice_cache
        else:
            p = shutil.which(c)
            if p:
                _soffice_cache = p
                return _soffice_cache
    _soffice_cache = False
    return None


def soffice_available():
    return find_soffice() is not None


def _run_soffice(args, timeout=600):
    soffice = find_soffice()
    if not soffice:
        raise RuntimeError("LibreOffice (soffice) is not installed on this server.")
    cmd = [soffice, "--headless", "--norestore", "--nologo", "--nodefault"]
    cmd += args
    with _lock:
        profile = tempfile.mkdtemp(prefix="loffice_")
        cmd += ["-env:UserInstallation=file:///" + profile.replace("\\", "/")]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            raise RuntimeError("LibreOffice conversion timed out.")
        finally:
            try:
                shutil.rmtree(profile, ignore_errors=True)
            except Exception:
                pass
    if proc.returncode != 0:
        raise RuntimeError("LibreOffice failed: " + (proc.stderr or proc.stdout or "").strip()[-2000:])
    return proc


def convert_to_pdf(src, out_dir):
    """Convert any LibreOffice-capable file to PDF (Linux fallback renderer)."""
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)
    _run_soffice(["--convert-to", "pdf", "--outdir", out_dir, os.path.abspath(src)])
    base = os.path.splitext(os.path.basename(src))[0]
    pdf = os.path.join(out_dir, base + ".pdf")
    if not os.path.exists(pdf):
        raise RuntimeError("LibreOffice did not produce a PDF for " + src)
    return pdf


def convert_docx_to(src_docx, out_format, out_path):
    """Convert a split docx to the target format.

    Uses MS Word COM when available; otherwise LibreOffice; otherwise only
    docx/docm (which are the Word package itself) can be produced.
    """
    fmt = out_format.lower().strip().lstrip(".")
    if fmt in ("docx", "docm"):
        # The trimming engine writes a complete Word package directly;
        # copying preserves the exact trimmed result (re-saving through Word
        # would re-insert trailing breaks, undoing the last-page trimming).
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        shutil.copyfile(src_docx, out_path)
        return out_path

    if word_com.word_available():
        return word_com.convert(src_docx, fmt, out_path)

    if soffice_available():
        out_dir = os.path.dirname(os.path.abspath(out_path))
        os.makedirs(out_dir, exist_ok=True)
        _run_soffice(["--convert-to", fmt, "--outdir", out_dir, os.path.abspath(src_docx)])
        base = os.path.splitext(os.path.basename(src_docx))[0]
        produced = os.path.join(out_dir, base + "." + fmt)
        if os.path.exists(produced):
            os.replace(produced, out_path)
            return out_path
        raise RuntimeError(f"LibreOffice did not produce .{fmt} output.")

    raise RuntimeError(
        f"Format '{fmt}' requires MS Word (Windows) or LibreOffice on the server."
    )


def normalize_to_docx(src, out_dir):
    """Convert a .doc/.rtf/.docm/.dotx file into a .docx for processing."""
    ext = os.path.splitext(src)[1].lower()
    if ext in (".docx", ".docm", ".dotx"):
        os.makedirs(out_dir, exist_ok=True)
        out = os.path.join(out_dir, "input_normalized.docx")
        shutil.copyfile(src, out)
        return out
    if ext == ".pdf":
        return None
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "input_normalized.docx")
    if word_com.word_available():
        word_com.convert(src, "docx", out)
        return out
    if soffice_available():
        _run_soffice(["--convert-to", "docx", "--outdir", out_dir, os.path.abspath(src)])
        base = os.path.splitext(os.path.basename(src))[0]
        produced = os.path.join(out_dir, base + ".docx")
        if not os.path.exists(produced):
            raise RuntimeError("Could not normalize file to docx.")
        return produced
    raise RuntimeError(
        "Normalizing this format requires MS Word (Windows) or LibreOffice on the server."
    )
