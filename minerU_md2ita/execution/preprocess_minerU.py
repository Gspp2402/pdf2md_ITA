#!/usr/bin/env python3
"""
Preprocess MinerU output using JSON-First approach (_content_list_v2.json / _content_list.json).
- Discards page_header, page_number, and page_aside_text automatically.
- Merges split titles and formats headings (#, ##, ###).
- Composes paragraphs with inline math ($...$).
- Preserves display math ($$...$$) and code blocks untouched.
- Translates image/table/chart captions and preserves relative paths.
- Splits document into cohesive section-level chunks (~10-15 chunks per chapter) in .tmp/<Chapter>/
- Prepares clean output directory output/<Book>/<Chapter>/ with images/.
"""

import os
import sys
import re
import json
import shutil
import argparse
from pathlib import Path


def parse_v2_json(v2_pages):
    """
    Parses MinerU _content_list_v2.json (list of page block lists) into a clean markdown structure.
    """
    md_blocks = []
    pending_title = None

    for page_blocks in v2_pages:
        for block in page_blocks:
            btype = block.get("type")
            content = block.get("content", {})

            # 1. Discard layout artifacts
            if btype in ("page_header", "page_number", "page_aside_text"):
                continue

            # 2. Section Titles
            if btype == "title":
                t_content = content.get("title_content", [])
                title_text = "".join(item.get("content", "") for item in t_content).strip()
                level = content.get("level", 2)

                # Fix OCR quirks
                title_text = re.sub(r"M<sub>ATLAB</sub>", "MATLAB", title_text)
                title_text = re.sub(r"M<sub>ODEL</sub>", "MODEL", title_text)

                if pending_title:
                    # Check if pending was a number (e.g. "11" or "11.2" or "11.2.1")
                    if re.match(r"^(\d+(\.\d+)*)$", pending_title["text"]):
                        combined_text = f"{pending_title['text']} {title_text}"
                        depth = len(pending_title["text"].split("."))
                        heading_hashes = "#" * max(1, min(6, depth))
                        md_blocks.append(f"\n\n{heading_hashes} {combined_text}\n\n")
                        pending_title = None
                        continue
                    else:
                        depth = pending_title.get("level", 2)
                        heading_hashes = "#" * max(1, min(6, depth))
                        md_blocks.append(f"\n\n{heading_hashes} {pending_title['text']}\n\n")
                        pending_title = None

                if re.match(r"^(\d+(\.\d+)*)$", title_text):
                    pending_title = {"text": title_text, "level": level}
                else:
                    heading_hashes = "#" * max(1, min(6, level))
                    md_blocks.append(f"\n\n{heading_hashes} {title_text}\n\n")
                continue

            if pending_title:
                depth = pending_title.get("level", 2)
                heading_hashes = "#" * max(1, min(6, depth))
                md_blocks.append(f"\n\n{heading_hashes} {pending_title['text']}\n\n")
                pending_title = None

            # 3. Paragraphs
            if btype == "paragraph":
                p_items = content.get("paragraph_content", [])
                p_text_parts = []
                for item in p_items:
                    itype = item.get("type")
                    icontent = item.get("content", "")
                    if itype == "text":
                        icontent = re.sub(r"M<sub>ATLAB</sub>", "MATLAB", icontent)
                        icontent = re.sub(r"M<sub>ODEL</sub>", "MODEL", icontent)
                        p_text_parts.append(icontent)
                    elif itype in ("equation_inline", "inline_equation"):
                        clean_math = icontent.strip().strip("$")
                        p_text_parts.append(f" ${clean_math}$ ")
                    else:
                        p_text_parts.append(icontent)

                full_p = "".join(p_text_parts)
                full_p = re.sub(r"\s+", " ", full_p).strip()
                full_p = re.sub(r"\s+([,.:;?!])", r"\1", full_p)
                full_p = re.sub(r"\$z\s*-\s*", "$z$-", full_p)
                if full_p:
                    md_blocks.append(f"{full_p}\n\n")
                continue

            # 4. Display Math Equations
            if btype in ("equation_interline", "equation", "interline_equation"):
                math_text = content.get("math_content", "") or block.get("text", "")
                math_text = math_text.strip()
                if not math_text.startswith("$$"):
                    math_text = f"$$\n{math_text}\n$$"
                md_blocks.append(f"\n{math_text}\n\n")
                continue

            # 5. Code Blocks
            if btype == "code":
                code_content = content.get("code_content", [])
                raw_code = "".join(item.get("content", "") for item in code_content)
                if not raw_code:
                    raw_code = block.get("code_body", "")
                raw_code = raw_code.strip()
                if not raw_code.startswith("```"):
                    raw_code = f"```matlab\n{raw_code}\n```"
                md_blocks.append(f"\n{raw_code}\n\n")
                continue

            # 6. Images and Charts
            if btype in ("image", "chart"):
                img_path = content.get("image_source", {}).get("path", "") or block.get("img_path", "")
                caption_items = content.get("image_caption", []) or content.get("chart_caption", []) or block.get("image_caption", [])
                
                caption_parts = []
                for cit in caption_items:
                    if isinstance(cit, dict):
                        caption_parts.append(cit.get("content", ""))
                    elif isinstance(cit, str):
                        caption_parts.append(cit)
                caption_text = "".join(caption_parts).strip()

                img_tag = f"![{caption_text}]({img_path})"
                if caption_text:
                    img_block = f"\n{img_tag}  \n{caption_text}\n\n"
                else:
                    img_block = f"\n{img_tag}\n\n"
                md_blocks.append(img_block)
                continue

            # 7. Tables
            if btype == "table":
                img_path = content.get("image_source", {}).get("path", "") or block.get("img_path", "")
                caption_items = content.get("table_caption", []) or block.get("table_caption", [])
                caption_parts = []
                for cit in caption_items:
                    if isinstance(cit, dict):
                        caption_parts.append(cit.get("content", ""))
                    elif isinstance(cit, str):
                        caption_parts.append(cit)
                caption_text = "".join(caption_parts).strip()

                if img_path:
                    table_block = f"\n![{caption_text}]({img_path})  \n{caption_text}\n\n"
                else:
                    table_body = content.get("html", "") or block.get("table_body", "")
                    table_block = f"\n{caption_text}\n\n{table_body}\n\n"
                md_blocks.append(table_block)
                continue

            # 8. Algorithm
            if btype == "algorithm":
                algo_items = content.get("algorithm_content", [])
                algo_parts = []
                for item in algo_items:
                    itype = item.get("type")
                    icontent = item.get("content", "")
                    if itype in ("equation_inline", "inline_equation"):
                        algo_parts.append(f" ${icontent.strip().strip('$')}$ ")
                    else:
                        algo_parts.append(icontent)
                algo_text = "".join(algo_parts).strip()
                if algo_text:
                    md_blocks.append(f"{algo_text}\n\n")
                continue

    if pending_title:
        depth = pending_title.get("level", 2)
        heading_hashes = "#" * max(1, min(6, depth))
        md_blocks.append(f"\n\n{heading_hashes} {pending_title['text']}\n\n")

    return md_blocks


def chunk_by_major_sections(md_blocks, target_chunk_chars=14000, max_chunk_chars=22000):
    """
    Groups markdown blocks into semantic chunks aligned with major sections (#, ##, ###)
    aiming for ~10-15 cohesive chunks per chapter.
    """
    chunks = []
    current_chunk = []
    current_chars = 0
    current_title = "Inizio"

    for block in md_blocks:
        stripped = block.strip()
        # Detect major headers (Level 1, 2, or 3)
        is_level1_or_2 = stripped.startswith("# ") or stripped.startswith("## ")
        is_level3 = stripped.startswith("### ")
        block_len = len(block)

        # Split on Level 1 or 2 if we have accumulated reasonable content
        if is_level1_or_2 and current_chars >= 6000:
            chunks.append({
                "title": current_title,
                "content": "".join(current_chunk).strip() + "\n"
            })
            current_chunk = [block]
            current_chars = block_len
            current_title = stripped.lstrip("#").strip().splitlines()[0]
        # Split on Level 3 if chunk is getting large
        elif is_level3 and current_chars >= target_chunk_chars:
            chunks.append({
                "title": current_title,
                "content": "".join(current_chunk).strip() + "\n"
            })
            current_chunk = [block]
            current_chars = block_len
            current_title = stripped.lstrip("#").strip().splitlines()[0]
        # Forced split on max chunk chars at any equation or blank
        elif current_chars + block_len >= max_chunk_chars and (stripped.startswith("$$") or stripped == "" or is_level3):
            chunks.append({
                "title": current_title,
                "content": "".join(current_chunk).strip() + "\n"
            })
            current_chunk = [block]
            current_chars = block_len
            if is_level1_or_2 or is_level3:
                current_title = stripped.lstrip("#").strip().splitlines()[0]
        else:
            current_chunk.append(block)
            current_chars += block_len

    if current_chunk:
        chunks.append({
            "title": current_title,
            "content": "".join(current_chunk).strip() + "\n"
        })

    return chunks


def win_long_path(p):
    p_str = str(Path(p).resolve())
    if os.name == 'nt' and not p_str.startswith('\\\\?\\'):
        return '\\\\?\\' + p_str
    return p_str


def preprocess_chapter(chapter_path, workspace_root="."):
    chapter_path = Path(chapter_path).resolve()
    if not os.path.exists(win_long_path(chapter_path)):
        print(f"Error: Chapter path not found: {chapter_path}")
        return False

    ha_dir = chapter_path / "hybrid_auto" if os.path.exists(win_long_path(chapter_path / "hybrid_auto")) else chapter_path
    
    parts = chapter_path.parts
    if "input" in parts:
        input_idx = parts.index("input")
        book_name = parts[input_idx + 1]
        chapter_name = parts[input_idx + 2] if len(parts) > input_idx + 2 else parts[-1]
    else:
        chapter_name = chapter_path.name
        book_name = chapter_path.parent.name

    print(f"=== Preprocessing JSON-First (Section-Level): {chapter_name} ({book_name}) ===")

    ha_dir_long = win_long_path(ha_dir)
    dir_entries = os.listdir(ha_dir_long)
    v2_files = [ha_dir / f for f in dir_entries if f.endswith("_content_list_v2.json")]
    v1_files = [ha_dir / f for f in dir_entries if f.endswith("_content_list.json")]
    md_files = [ha_dir / f for f in dir_entries if f.endswith(".md")]

    if v2_files:
        print(f"Using MinerU V2 JSON: {v2_files[0].name}")
        with open(win_long_path(v2_files[0]), "r", encoding="utf-8") as f:
            v2_data = json.load(f)
        md_blocks = parse_v2_json(v2_data)
    elif v1_files:
        print(f"Using MinerU V1 JSON: {v1_files[0].name}")
        with open(win_long_path(v1_files[0]), "r", encoding="utf-8") as f:
            v1_data = json.load(f)
        md_blocks = []
        for it in v1_data:
            itype = it.get("type")
            if itype in ("header", "page_number", "aside_text"):
                continue
            if itype == "text":
                txt = it.get("text", "")
                level = it.get("text_level", 0)
                if level:
                    md_blocks.append(f"\n\n{'#' * level} {txt}\n\n")
                else:
                    md_blocks.append(f"{txt}\n\n")
            elif itype == "equation":
                md_blocks.append(f"\n{it.get('text', '')}\n\n")
            elif itype in ("image", "chart", "table"):
                path = it.get("img_path", "")
                cap = "".join(it.get("image_caption", []) or it.get("chart_caption", []) or it.get("table_caption", []))
                md_blocks.append(f"\n![{cap}]({path})  \n{cap}\n\n")
            elif itype == "code":
                md_blocks.append(f"\n{it.get('code_body', '')}\n\n")
    elif md_files:
        print(f"Fallback to raw Markdown: {md_files[0].name}")
        with open(win_long_path(md_files[0]), "r", encoding="utf-8") as f:
            md_blocks = [f.read()]
    else:
        print(f"Error: No content file found in {ha_dir}")
        return False

    chunks = chunk_by_major_sections(md_blocks)

    tmp_dir = Path(workspace_root) / ".tmp" / book_name / chapter_name
    tmp_dir_long = win_long_path(tmp_dir)
    # Clean previous chunks in tmp_dir
    if os.path.exists(tmp_dir_long):
        shutil.rmtree(tmp_dir_long)
    os.makedirs(tmp_dir_long, exist_ok=True)

    manifest = {
        "book_name": book_name,
        "chapter_name": chapter_name,
        "total_chunks": len(chunks),
        "chunks": []
    }

    for idx, chunk in enumerate(chunks, 1):
        chunk_file = tmp_dir / f"chunk_{idx:03d}.md"
        with open(win_long_path(chunk_file), "w", encoding="utf-8") as f:
            f.write(chunk["content"])
        manifest["chunks"].append({
            "index": idx,
            "title": chunk["title"],
            "file": str(chunk_file.name),
            "lines": len(chunk["content"].splitlines()),
            "chars": len(chunk["content"])
        })

    with open(win_long_path(tmp_dir / "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    # Output directory
    output_book_dir = Path(workspace_root) / "output" / book_name
    output_chapter_dir = output_book_dir / chapter_name
    os.makedirs(win_long_path(output_chapter_dir), exist_ok=True)

    # Copy images folder ONLY
    source_images = ha_dir / "images"
    target_images = output_chapter_dir / "images"
    if os.path.exists(win_long_path(source_images)):
        if os.path.exists(win_long_path(target_images)):
            shutil.rmtree(win_long_path(target_images))
        shutil.copytree(win_long_path(source_images), win_long_path(target_images))
        print(f"Copied images to deliverable folder: {target_images}")

    print(f"Preprocessing completed successfully!")
    print(f"Created {len(chunks)} cohesive section-level chunks in {tmp_dir}")
    print(f"Target directory ready: {output_chapter_dir} (Contains only images/)")
    return True


def main():
    parser = argparse.ArgumentParser(description="Preprocess MinerU using JSON-First approach with section-level chunking.")
    parser.add_argument("--chapter", required=True, help="Path to chapter folder in input/")
    parser.add_argument("--workspace", default=".", help="Workspace root directory")
    args = parser.parse_args()

    success = preprocess_chapter(args.chapter, args.workspace)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
