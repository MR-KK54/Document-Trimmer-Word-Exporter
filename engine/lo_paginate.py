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


def _page_words(raw_text):
    """Tokenize extracted PDF text like the docx fingerprinting does.

    Merges hyphenated line breaks (word-\\nbreak -> wordbreak) and reduces every
    token to [a-z0-9]+, so comparisons between unit fingerprints and page text
    are apples-to-apples regardless of case, punctuation or line wrapping.
    """
    tokens = raw_text.split()
    merged = []
    i = 0
    while i < len(tokens):
        t = tokens[i]
        while t.endswith("-") and i + 1 < len(tokens):
            t = t[:-1] + tokens[i + 1]
            i += 1
        merged.extend(re.findall(r"[a-z0-9]+", t.lower()))
        i += 1
    return merged


def _prefix_match_len(fp_words, page_words):
    """Longest k such that fp_words[:k] appear in order inside page_words."""
    k = 0
    idx = 0
    for w in fp_words:
        try:
            idx = page_words.index(w, idx)
        except ValueError:
            break
        idx += 1
        k += 1
    return k


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
            page_words_list = [_page_words(doc[i].get_text()) for i in range(doc.page_count)]
        if not page_words_list:
            return None

        # Fingerprint: the opening words of each unit (as word tokens).
        fingerprints = []
        for u in units:
            node = u["node"] if u["kind"] == "p" else u["row"]
            fingerprints.append(_strip_punct(_element_text(node))[:8])

        unit_page = []
        page_idx = 0  # monotonic forward search
        for fp in fingerprints:
            if not fp:
                unit_page.append(page_idx + 1)
                continue
            best_k = 0
            best_page = page_idx
            for pi in range(page_idx, len(page_words_list)):
                k = _prefix_match_len(fp, page_words_list[pi])
                if k > best_k:
                    best_k = k
                    best_page = pi
                    if k == len(fp):
                        break
            # Only trust a move when at least the first word matched; otherwise
            # keep the previous page (e.g. table cell boundaries, odd glyphs).
            if best_k >= 1:
                page_idx = best_page
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
