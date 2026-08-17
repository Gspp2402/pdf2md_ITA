#!/usr/bin/env python3
"""
inspect_pdf.py
Deterministic tool for inspecting a PDF file:
- Extracts total page count, TOC/bookmarks, and metadata into meta.json
- Extracts page-by-page text into pages_text.json
- Renders initial and final pages as high-quality PNG images into page_images/ for visual inspection
"""

import os
import sys
import json
import argparse
from pathlib import Path

try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz
    except ImportError:
        print("Error: PyMuPDF is required. Please run: pip install pymupdf", file=sys.stderr)
        sys.exit(1)


def inspect_pdf(
    pdf_path: str,
    output_dir: str = None,
    render_start_pages: int = 35,
    render_end_pages: int = 25,
    dpi: int = 150,
    render_all: bool = False
):
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    book_name = pdf_file.stem.strip()
    if output_dir is None:
        target_dir = Path(".tmp") / book_name
    else:
        target_dir = Path(output_dir)

    target_dir.mkdir(parents=True, exist_ok=True)
    images_dir = target_dir / "page_images"
    images_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(pdf_file)
    total_pages = len(doc)

    # 1. Metadata and TOC
    toc = doc.get_toc()  # [[lvl, title, page, ...], ...]
    meta = {
        "book_name": book_name,
        "source_pdf": str(pdf_file.resolve()),
        "total_pages": total_pages,
        "has_toc_bookmarks": bool(toc),
        "toc": toc,
        "pdf_metadata": doc.metadata
    }

    meta_file = target_dir / "meta.json"
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    # 2. Page Text Extraction
    pages_text = []
    for i, page in enumerate(doc):
        text = page.get_text()
        pages_text.append({
            "page": i + 1,
            "char_count": len(text.strip()),
            "text": text
        })

    text_file = target_dir / "pages_text.json"
    with open(text_file, "w", encoding="utf-8") as f:
        json.dump(pages_text, f, indent=2, ensure_ascii=False)

    # 3. Page Rendering to PNG
    # Determine which pages to render
    if render_all or total_pages <= (render_start_pages + render_end_pages):
        pages_to_render = range(total_pages)
    else:
        start_range = set(range(min(render_start_pages, total_pages)))
        end_start_idx = max(0, total_pages - render_end_pages)
        end_range = set(range(end_start_idx, total_pages))
        pages_to_render = sorted(list(start_range.union(end_range)))

    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)

    rendered_images = []
    for page_idx in pages_to_render:
        page = doc[page_idx]
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        img_name = f"page_{page_idx + 1}.png"
        img_path = images_dir / img_name
        pix.save(str(img_path))
        rendered_images.append({
            "page": page_idx + 1,
            "image_file": str(img_path)
        })

    doc.close()

    summary = {
        "status": "success",
        "book_name": book_name,
        "total_pages": total_pages,
        "has_toc_bookmarks": bool(toc),
        "output_dir": str(target_dir.resolve()),
        "meta_file": str(meta_file.resolve()),
        "text_file": str(text_file.resolve()),
        "rendered_pages_count": len(rendered_images)
    }

    print(json.dumps(summary, indent=2))
    return summary


def main():
    parser = argparse.ArgumentParser(description="Inspect a PDF file and extract TOC, text, and page images.")
    parser.add_argument("--input", "-i", required=True, help="Path to the source PDF file")
    parser.add_argument("--output-dir", "-o", default=None, help="Directory to store intermediate inspection files")
    parser.add_argument("--render-start", type=int, default=35, help="Number of initial pages to render as images (default: 35)")
    parser.add_argument("--render-end", type=int, default=25, help="Number of ending pages to render as images (default: 25)")
    parser.add_argument("--dpi", type=int, default=150, help="DPI resolution for rendered images (default: 150)")
    parser.add_argument("--render-all", action="store_true", help="Render all pages in the PDF")

    args = parser.parse_args()

    try:
        inspect_pdf(
            pdf_path=args.input,
            output_dir=args.output_dir,
            render_start_pages=args.render_start,
            render_end_pages=args.render_end,
            dpi=args.dpi,
            render_all=args.render_all
        )
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
