"""
file_processor.py
Robust file loader and text extraction engine.
Supports:
- PDF (.pdf) via PyMuPDF (fitz)
- Word Documents (.docx) via python-docx
- Text files (.txt, .md, .json, .csv)
"""

import os
import io
import re
from typing import Dict, Any, List

def extract_text_from_pdf(file_source) -> Dict[str, Any]:
    """
    Extracts text, metadata, and outline from a PDF file.
    file_source can be a file path (str) or a file-like object (bytes / BytesIO).
    """
    import fitz
    
    if isinstance(file_source, (str, os.PathLike)):
        doc = fitz.open(file_source)
        filename = os.path.basename(file_source)
    else:
        file_bytes = file_source.read() if hasattr(file_source, "read") else file_source
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        filename = getattr(file_source, "name", "uploaded_file.pdf")
        
    total_pages = len(doc)
    pages_text: List[str] = []
    headings: List[str] = []
    
    # Check for embedded TOC
    toc = doc.get_toc()
    if toc:
        for item in toc:
            # item format: [lvl, title, page, ...]
            if len(item) >= 2 and item[1]:
                headings.append(str(item[1]).strip())

    for page_idx in range(total_pages):
        page = doc[page_idx]
        text = page.get_text("text")
        pages_text.append(text)
        
        # If no embedded TOC, heuristically detect headings
        if not toc:
            blocks = page.get_text("blocks")
            for b in blocks:
                block_text = b[4].strip() if len(b) > 4 else ""
                # Single or two short lines that look like a heading
                lines = [l.strip() for l in block_text.splitlines() if l.strip()]
                if 1 <= len(lines) <= 2:
                    line = lines[0]
                    if len(line) < 80 and re.match(r'^(Chapter|Section|\d+(\.\d+)*|[A-Z][A-Za-z0-9\s]{3,50})$', line):
                        headings.append(line)
                        
    doc.close()
    
    full_text = "\n\n".join(pages_text)
    words = re.findall(r'\b\w+\b', full_text)
    
    return {
        "filename": filename,
        "file_type": "PDF",
        "total_pages": total_pages,
        "word_count": len(words),
        "char_count": len(full_text),
        "headings": headings[:50],
        "has_embedded_toc": bool(toc),
        "full_text": full_text,
        "pages_text": pages_text
    }

def extract_text_from_docx(file_source) -> Dict[str, Any]:
    """
    Extracts text and headings from a .docx file.
    """
    import docx
    
    if isinstance(file_source, (str, os.PathLike)):
        doc = docx.Document(file_source)
        filename = os.path.basename(file_source)
    else:
        file_bytes = file_source.read() if hasattr(file_source, "read") else file_source
        doc = docx.Document(io.BytesIO(file_bytes))
        filename = getattr(file_source, "name", "uploaded_file.docx")
        
    paragraphs = []
    headings = []
    
    for p in doc.paragraphs:
        txt = p.text.strip()
        if not txt:
            continue
        paragraphs.append(txt)
        if p.style and "Heading" in p.style.name:
            headings.append(txt)
            
    full_text = "\n\n".join(paragraphs)
    words = re.findall(r'\b\w+\b', full_text)
    
    return {
        "filename": filename,
        "file_type": "DOCX",
        "total_pages": max(1, len(paragraphs) // 10),
        "word_count": len(words),
        "char_count": len(full_text),
        "headings": headings[:50],
        "has_embedded_toc": len(headings) > 0,
        "full_text": full_text,
        "paragraphs": paragraphs
    }

def extract_text_from_plain(file_source, ext="txt") -> Dict[str, Any]:
    """
    Extracts text from plain text or markdown files.
    """
    if isinstance(file_source, (str, os.PathLike)):
        filename = os.path.basename(file_source)
        with open(file_source, "r", encoding="utf-8", errors="ignore") as f:
            full_text = f.read()
    else:
        filename = getattr(file_source, "name", f"uploaded_file.{ext}")
        raw = file_source.read() if hasattr(file_source, "read") else file_source
        if isinstance(raw, bytes):
            try:
                full_text = raw.decode("utf-8")
            except UnicodeDecodeError:
                full_text = raw.decode("latin-1", errors="ignore")
        else:
            full_text = str(raw)
            
    # Markdown headings
    headings = re.findall(r'^#{1,3}\s+(.+)$', full_text, flags=re.MULTILINE)
    words = re.findall(r'\b\w+\b', full_text)
    
    return {
        "filename": filename,
        "file_type": ext.upper(),
        "total_pages": max(1, len(words) // 500),
        "word_count": len(words),
        "char_count": len(full_text),
        "headings": headings[:50],
        "has_embedded_toc": len(headings) > 0,
        "full_text": full_text
    }

def process_uploaded_file(file_source, filename: str = "") -> Dict[str, Any]:
    """
    Generic dispatcher that accepts any uploaded file or file path.
    """
    fname = filename or getattr(file_source, "name", "")
    if isinstance(file_source, (str, os.PathLike)):
        fname = str(file_source)
        
    lower_name = fname.lower()
    
    if lower_name.endswith(".pdf"):
        return extract_text_from_pdf(file_source)
    elif lower_name.endswith((".docx", ".doc")):
        return extract_text_from_docx(file_source)
    elif lower_name.endswith((".txt", ".md", ".json", ".csv", ".tsv", ".html")):
        ext = lower_name.split(".")[-1]
        return extract_text_from_plain(file_source, ext=ext)
    else:
        # Default try plain text
        return extract_text_from_plain(file_source, ext="txt")

