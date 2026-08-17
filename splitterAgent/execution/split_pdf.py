#!/usr/bin/env python3
"""
split_pdf.py
Deterministic tool for splitting a PDF based on a structured chapters_map.json:
- Extracts 0_indice_generale.pdf
- Extracts 0_indice_analitico.pdf (if present)
- Extracts 1_<nome_capitolo>.pdf, 2_<nome_capitolo>.pdf, etc.
- Automatically redacts trailing 'References' / 'Bibliography' from the last page of chapters
- Preserves full PDF vector quality and annotations
"""

import os
import re
import sys
import json
import argparse
import shutil
from pathlib import Path

try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz
    except ImportError:
        print("Error: PyMuPDF is required. Please run: pip install pymupdf", file=sys.stderr)
        sys.exit(1)


def sanitize_filename(name: str) -> str:
    """Sanitize string to be safe for filenames across operating systems."""
    # Replace illegal characters
    cleaned = re.sub(r'[\\/*?:"<>|]', "", name)
    # Replace multiple spaces/underscores
    cleaned = re.sub(r'\s+', "_", cleaned.strip())
    cleaned = re.sub(r'_+', "_", cleaned)
    return cleaned


def redact_trailing_references(page: fitz.Page, keywords=(
    "References", "Bibliography", "Bibliografia", "Riferimenti bibliografici",
    "Further Reading", "Further Readings", "Suggested Reading", "Suggested Readings",
    "Letture consigliate", "Fonti bibliografiche", "Note bibliografiche"
)) -> bool:
    """
    Search for a trailing references/bibliography section heading on the page
    and redact everything from that heading down to the bottom of the page.
    """
    for kw in keywords:
        rects = page.search_for(kw)
        if rects:
            # Pick the last match (often heading near middle/bottom of last page)
            r = rects[-1]
            # Redact from top of heading to bottom of page
            redact_rect = fitz.Rect(0, max(0, r.y0 - 3), page.rect.width, page.rect.height)
            page.add_redact_annot(redact_rect, fill=(1, 1, 1))
            page.apply_redactions()
            return True
    return False


def extract_pages_to_pdf(
    src_doc: fitz.Document,
    page_numbers: list[int],
    output_file: Path,
    redact_trailing_refs: bool = False
):
    """
    Extract specific 1-indexed page numbers from src_doc and save to output_file.
    Optionally redacts trailing references on the final extracted page.
    """
    output_file.parent.mkdir(parents=True, exist_ok=True)
    dst_doc = fitz.open()

    total_doc_pages = len(src_doc)
    for p_num in page_numbers:
        if 1 <= p_num <= total_doc_pages:
            dst_doc.insert_pdf(src_doc, from_page=p_num - 1, to_page=p_num - 1)
        else:
            raise ValueError(f"Page number {p_num} out of bounds (1..{total_doc_pages})")

    # Apply redaction to last page if requested
    if redact_trailing_refs and len(dst_doc) > 0:
        last_page = dst_doc[-1]
        redact_trailing_references(last_page)

    dst_doc.save(str(output_file))
    dst_doc.close()


def parse_page_spec(spec) -> list[int]:
    """Parse page specification which can be a list of ints [1, 2, 3] or a range [start, end]."""
    if isinstance(spec, list):
        if len(spec) == 2 and isinstance(spec[0], int) and isinstance(spec[1], int) and spec[1] >= spec[0]:
            return list(range(spec[0], spec[1] + 1))
        return [int(p) for p in spec]
    elif isinstance(spec, dict) and "start_page" in spec and "end_page" in spec:
        return list(range(int(spec["start_page"]), int(spec["end_page"]) + 1))
    elif isinstance(spec, int):
        return [spec]
    raise ValueError(f"Invalid page specification: {spec}")


def split_pdf_by_map(map_path: str, custom_output_dir: str = None, cleanup_tmp: bool = False) -> dict:
    map_file = Path(map_path)
    if not map_file.exists():
        raise FileNotFoundError(f"JSON map file not found: {map_path}")

    with open(map_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    book_name = data.get("book_name", map_file.stem)
    source_pdf_str = data.get("source_pdf")
    if not source_pdf_str:
        raise ValueError("Field 'source_pdf' missing in JSON map.")

    source_pdf = Path(source_pdf_str)
    if not source_pdf.exists():
        # Try resolving relative to map file parent or project root
        alt_path = map_file.parent / source_pdf
        if alt_path.exists():
            source_pdf = alt_path
        else:
            alt_path_input = Path("input") / source_pdf.name
            if alt_path_input.exists():
                source_pdf = alt_path_input
            else:
                raise FileNotFoundError(f"Source PDF not found at {source_pdf_str}")

    if custom_output_dir:
        out_dir = Path(custom_output_dir)
    else:
        out_dir = Path("output") / sanitize_filename(book_name)

    out_dir.mkdir(parents=True, exist_ok=True)

    src_doc = fitz.open(source_pdf)
    total_pages = len(src_doc)
    generated_files = []

    # Global redaction default (default: True)
    global_redact_refs = data.get("redact_trailing_references", True)

    # 1. Process Indices
    indices = data.get("indices", {})
    if indices:
        # General Index (Sommario)
        indice_gen = indices.get("indice_generale")
        if indice_gen:
            filename = indice_gen.get("filename", "0_indice_generale.pdf")
            pages = indice_gen.get("pages")
            if not pages and "start_page" in indice_gen and "end_page" in indice_gen:
                pages = list(range(indice_gen["start_page"], indice_gen["end_page"] + 1))
            
            if pages:
                target_file = out_dir / sanitize_filename(filename)
                extract_pages_to_pdf(src_doc, pages, target_file, redact_trailing_refs=False)
                generated_files.append({
                    "type": "indice_generale",
                    "filename": target_file.name,
                    "pages": pages,
                    "page_count": len(pages),
                    "path": str(target_file.resolve())
                })

        # Analytical Index (Indice Analitico)
        indice_ana = indices.get("indice_analitico")
        if indice_ana:
            filename = indice_ana.get("filename", "0_indice_analitico.pdf")
            pages = indice_ana.get("pages")
            if not pages and "start_page" in indice_ana and "end_page" in indice_ana:
                pages = list(range(indice_ana["start_page"], indice_ana["end_page"] + 1))
            
            if pages:
                target_file = out_dir / sanitize_filename(filename)
                extract_pages_to_pdf(src_doc, pages, target_file, redact_trailing_refs=False)
                generated_files.append({
                    "type": "indice_analitico",
                    "filename": target_file.name,
                    "pages": pages,
                    "page_count": len(pages),
                    "path": str(target_file.resolve())
                })

    # 2. Process Chapters
    chapters = data.get("chapters", [])
    for idx, chap in enumerate(chapters, 1):
        chap_num = chap.get("index", idx)
        title = chap.get("title", f"Capitolo_{chap_num}")
        
        # Calculate page numbers
        if "pages" in chap:
            pages = chap["pages"]
        elif "start_page" in chap and "end_page" in chap:
            pages = list(range(int(chap["start_page"]), int(chap["end_page"]) + 1))
        else:
            raise ValueError(f"Chapter {title} missing 'pages' or 'start_page'/'end_page'")

        filename = chap.get("filename")
        if not filename:
            clean_title = sanitize_filename(title)
            filename = f"{chap_num}_{clean_title}.pdf"
        else:
            filename = sanitize_filename(filename)
            if not filename.lower().endswith(".pdf"):
                filename += ".pdf"

        # Check chapter-level redaction override or fallback to global default
        chap_redact = chap.get("redact_trailing_references", global_redact_refs)

        target_file = out_dir / filename
        extract_pages_to_pdf(src_doc, pages, target_file, redact_trailing_refs=chap_redact)
        generated_files.append({
            "type": "chapter",
            "index": chap_num,
            "title": title,
            "filename": target_file.name,
            "pages": [min(pages), max(pages)] if pages else [],
            "page_count": len(pages),
            "trailing_references_redacted": chap_redact,
            "path": str(target_file.resolve())
        })

    src_doc.close()

    # Save a copy of chapters_map.json into output directory for provenance
    out_map_file = out_dir / "chapters_map.json"
    with open(out_map_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # Optional cleanup of intermediate .tmp directory
    if cleanup_tmp:
        tmp_dir = map_file.parent
        if tmp_dir.exists() and ".tmp" in str(tmp_dir.resolve()):
            shutil.rmtree(tmp_dir, ignore_errors=True)

    result = {
        "status": "success",
        "book_name": book_name,
        "source_pdf": str(source_pdf.resolve()),
        "output_directory": str(out_dir.resolve()),
        "total_source_pages": total_pages,
        "generated_files_count": len(generated_files),
        "files": generated_files,
        "map_saved_at": str(out_map_file.resolve()),
        "tmp_cleaned": cleanup_tmp
    }

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result


def main():
    parser = argparse.ArgumentParser(description="Split PDF into indices and chapters according to a chapters_map.json.")
    parser.add_argument("--map", "-m", required=True, help="Path to chapters_map.json")
    parser.add_argument("--output-dir", "-o", default=None, help="Custom output directory")
    parser.add_argument("--cleanup-tmp", action="store_true", help="Remove intermediate .tmp directory after successful split")

    args = parser.parse_args()

    try:
        split_pdf_by_map(map_path=args.map, custom_output_dir=args.output_dir, cleanup_tmp=args.cleanup_tmp)
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
