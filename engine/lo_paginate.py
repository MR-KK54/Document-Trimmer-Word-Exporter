"""LibreOffice-based pagination for Linux/Render.

When a document was not saved by MS Word (no <w:lastRenderedPageBreak/>
markers), the marker engine cannot reproduce Word's natural text flow. This
module uses LibreOffice as a real layout engine: it converts the docx to PDF,
then maps every content unit (paragraph / table row) to the PDF page where the
unit's opening words first appear. The resulting boundaries reproduce the
layout engine's pagination instead of guessing from explicit breaks.
"""

import os
import re
import shutil
import tempfile

import pymupdf

from . import convert
from .docx_trim import build_units, _q, _strip_punct, _element_text, load_document_xml


def paginate_with_libreoffice(docx_path):
    if not convert.soffice_available():
        return None

    try:
        root = load_document_xml(docx_path)
    except Exception:
        return None
    body = root.find(_q("body"))
    if body is None:
        return None
    units = build_units(body)
    if not units:
        return None

    tmp = tempfile.mkdtemp(prefix="lo_pag_")
    try:
        pdf = convert.convert_to_pdf(docx_path, tmp)
        with pymupdf.open(pdf) as doc:
            page_texts = []
            for i in range(doc.page_count):
                page_texts.append(re.sub(r"\s+", " ", doc[i].get_text()))
        if not page_texts:
            return None

        # Fingerprint: the opening words of each unit (searchable across pages).
        fingerprints = []
        for u in units:
            node = u["node"] if u["kind"] == "p" else u["row"]
            words = _strip_punct(_element_text(node))[:8]
            fingerprints.append(" ".join(words))

        unit_page = []
        page_idx = 0  # monotonic forward search
        for fp in fingerprints:
            if not fp:
                unit_page.append(page_idx + 1)
                continue
            moved = False
            for pi in range(page_idx, len(page_texts)):
                if fp in page_texts[pi]:
                    page_idx = pi
                    moved = True
                    break
            if not moved:
                # Fall back to first word only (e.g. text split by hyphenation).
                first = fp.split()[0]
                for pi in range(page_idx, len(page_texts)):
                    if first in page_texts[pi]:
                        page_idx = pi
                        break
            unit_page.append(page_idx + 1)

        page_count = max(unit_page)
        by_page = {}
        for i, p in enumerate(unit_page):
            by_page.setdefault(p, []).append(i)
        boundaries = []
        last = -1
        for p in range(1, page_count + 1):
            lst = by_page.get(p)
            if lst:
                last = max(last, max(lst))
            boundaries.append(last)
        return page_count, boundaries
    finally:
        try:
            shutil.rmtree(tmp, ignore_errors=True)
        except Exception:
            pass
