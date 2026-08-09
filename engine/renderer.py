"""Document preview rendering (page -> PNG).

On Windows the docx is rendered through MS Word (Word COM) so previews match
Word exactly. On Linux (Render) LibreOffice is used only as a renderer when
available. PDFs are rendered directly with PyMuPDF.
"""

import hashlib
import io
import os
import tempfile

import pymupdf

from . import convert, word_com


class Renderer:
    def __init__(self, cache_dir):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

    def _cache_key(self, path):
        st = os.stat(path)
        key = f"{os.path.basename(path)}-{st.st_mtime_ns}-{st.st_size}"
        return hashlib.md5(key.encode()).hexdigest()

    def _pdf_for(self, path):
        """Return a PDF file for a document (converting when needed)."""
        ext = os.path.splitext(path)[1].lower()
        if ext == ".pdf":
            return path, True
        key = self._cache_key(path)
        pdf = os.path.join(self.cache_dir, key + ".pdf")
        if not os.path.exists(pdf):
            tmp = tempfile.mkdtemp(prefix="render_")
            try:
                if word_com.word_available():
                    word_com.export_pdf(path, pdf)
                elif convert.soffice_available():
                    produced = convert.convert_to_pdf(path, tmp)
                    os.replace(produced, pdf)
                else:
                    raise RuntimeError(
                        "No document renderer available. MS Word (Windows) or LibreOffice is required for previews."
                    )
            finally:
                import shutil

                shutil.rmtree(tmp, ignore_errors=True)
        return pdf, False

    def render_page(self, path, page, width):
        """Return (png_bytes, total_pages). page is 1-indexed."""
        pdf, _ = self._pdf_for(path)
        with pymupdf.open(pdf) as doc:
            total = doc.page_count
            page = max(1, min(page, total))
            pg = doc[page - 1]
            zoom = max(0.5, (width or 1200) / 1200)
            pix = pg.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
            buf = io.BytesIO(pix.tobytes("png"))
        return buf.getvalue(), total
