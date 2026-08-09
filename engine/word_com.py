"""MS Word COM engine - the authoritative, high-fidelity Word engine.

Runs only on Windows with Microsoft Word installed. Used for:
  * True Word pagination (page boundaries via Word's own layout engine).
  * Format conversion (docx / doc / rtf / pdf / docm) via Word's SaveAs.
  * PDF export for document previews.

Every function degrades gracefully when Word is unavailable.
"""

import os
import re
import unicodedata

_win32com = None
_pythoncom = None
_word_checked = False
_word_ok = False


def _load_word():
    global _win32com, _pythoncom, _word_checked, _word_ok
    if _word_checked:
        return _win32com if _word_ok else None
    _word_checked = True
    if os.name != "nt":
        return None
    try:
        import pythoncom
        import win32com.client  # noqa

        _pythoncom = pythoncom
        _win32com = win32com.client
        _word_ok = True
    except Exception:
        _win32com = None
        _pythoncom = None
        _word_ok = False
    return _win32com if _word_ok else None


def word_available():
    return _load_word() is not None


def _open_word():
    if not word_available():
        raise RuntimeError("MS Word (win32com) is not available on this server.")
    pythoncom = _pythoncom
    pythoncom.CoInitialize()
    word = _win32com.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    try:
        word.AutomationSecurity = 3  # msoAutomationSecurityForceDisable
    except Exception:
        pass
    try:
        word.Options.ConfirmConversions = False
    except Exception:
        pass
    return word


def _shutdown_word(word):
    try:
        word.Quit()
    except Exception:
        pass
    try:
        _pythoncom.CoUninitialize()
    except Exception:
        pass


def _open_doc(word, path, readonly=True):
    return word.Documents.Open(
        FileName=os.path.abspath(path),
        ReadOnly=readonly,
        AddToRecentFiles=False,
        Visible=False,
        ConfirmConversions=False,
        Revert=False,
    )


def _norm(text):
    text = unicodedata.normalize("NFKC", text or "").lower()
    return re.findall(r"[a-z0-9]+", text)


def paginate(docx_path):
    """Return (page_count, boundaries) using MS Word's real layout engine.

    boundaries[page0] = last content-unit index on that page.
    """
    word = _open_word()
    doc = None
    try:
        doc = _open_doc(word, docx_path, readonly=True)
        doc.Repaginate()
        page_count = int(doc.ComputeStatistics(2))  # wdStatisticPages

        # Gather (start_char_pos, words, end_page) for every top-level paragraph
        # and every table row in document order, merged by character position.
        entries = []
        try:
            for para in doc.Paragraphs:
                if para.Range.Tables.Count > 0:
                    continue  # paragraph lives inside a table cell
                rng = para.Range
                text = rng.Text or ""
                if text.endswith("\r"):
                    text = text[:-1]
                page = int(rng.Information(3))  # wdActiveEndPageNumber
                entries.append((int(rng.Start), _norm(text), page))
        except Exception:
            entries = []
            try:
                for i in range(1, doc.Paragraphs.Count + 1):
                    para = doc.Paragraphs(i)
                    if para.Range.Tables.Count > 0:
                        continue
                    rng = para.Range
                    text = (rng.Text or "").rstrip("\r")
                    page = int(rng.Information(3))
                    entries.append((int(rng.Start), _norm(text), page))
            except Exception:
                pass

        try:
            for t in range(1, doc.Tables.Count + 1):
                tbl = doc.Tables(t)
                for r in range(1, tbl.Rows.Count + 1):
                    row = tbl.Rows(r)
                    rng = row.Range
                    text = (rng.Text or "").rstrip("\r\x07")
                    page = int(rng.Information(3))
                    entries.append((int(rng.Start), _norm(text), page))
        except Exception:
            pass

        entries.sort(key=lambda e: e[0])
        items = [(w, p) for _, w, p in entries]
        page_count = max(page_count, max([p for _, p in items] + [1]))
        return page_count, _unit_end_pages_to_boundaries(items, page_count)
    finally:
        try:
            if doc is not None:
                doc.Close(SaveChanges=0)
        except Exception:
            pass
        _shutdown_word(word)


def _unit_end_pages_to_boundaries(items, page_count):
    """items: [(unit_words, end_page)] aligned 1:1 with XML content units.

    Returns boundaries[page0] = last unit index on that page.
    """
    by_page = {}
    for u, (_w, p) in enumerate(items):
        by_page.setdefault(p, []).append(u)
    boundaries = []
    last = -1
    for p in range(1, page_count + 1):
        lst = by_page.get(p)
        if lst:
            last = max(last, max(lst))
        boundaries.append(last)
    return boundaries


_SAVE_FORMAT = {
    "docx": 12,  # wdFormatXMLDocument
    "doc": 0,  # wdFormatDocument
    "rtf": 6,  # wdFormatRTF
    "docm": 13,  # wdFormatXMLDocumentMacroEnabled
    "dotx": 7,
    "dotm": 9,
    "txt": 2,
    "odt": 23,
}


def convert(src_path, out_format, out_path):
    """Convert a Word-family document to the target format using Word SaveAs."""
    fmt = out_format.lower().strip().lstrip(".")
    out_path = os.path.abspath(out_path)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    if os.path.exists(out_path):
        os.remove(out_path)

    word = _open_word()
    doc = None
    try:
        doc = _open_doc(word, src_path, readonly=False)
        if fmt == "pdf":
            doc.ExportAsFixedFormat(
                OutputFileName=out_path,
                ExportFormat=17,  # wdExportFormatPDF
                OpenAfterExport=False,
                OptimizeFor=0,
                CreateBookmarks=1,
                DocStructureTags=True,
            )
        elif fmt in _SAVE_FORMAT:
            doc.SaveAs(out_path, FileFormat=_SAVE_FORMAT[fmt])
        else:
            raise ValueError(f"Unsupported format for MS Word conversion: {out_format}")
    finally:
        try:
            if doc is not None:
                doc.Close(SaveChanges=0)
        except Exception:
            pass
        _shutdown_word(word)
    if not os.path.exists(out_path):
        raise RuntimeError("MS Word did not produce the converted file.")
    return out_path


def export_pdf(src_path, out_pdf):
    """Export a Word-family document to PDF (for previews)."""
    return convert(src_path, "pdf", out_pdf)
