#!/usr/bin/env python3
"""
Assemble translated chunks into the final chapter markdown file in output/<Book>/<Chapter>/<Chapter>.md.
Enforces the deliverable rule: only <Chapter>.md and images/ in output/<Book>/<Chapter>/.
"""

import os
import sys
import json
import argparse
from pathlib import Path


def win_long_path(p):
    p_str = str(Path(p).resolve())
    if os.name == 'nt' and not p_str.startswith('\\\\?\\'):
        return '\\\\?\\' + p_str
    return p_str


def assemble_chapter(chapter_name, book_name=None, workspace_root=".", allow_partial=False):
    ws = Path(workspace_root).resolve()
    
    # Check .tmp/book_name/chapter_name first, then .tmp/chapter_name
    tmp_dir = None
    if book_name and os.path.exists(win_long_path(ws / ".tmp" / book_name / chapter_name / "manifest.json")):
        tmp_dir = ws / ".tmp" / book_name / chapter_name
    elif os.path.exists(win_long_path(ws / ".tmp" / chapter_name / "manifest.json")):
        tmp_dir = ws / ".tmp" / chapter_name
    else:
        # Search all book subfolders in .tmp
        tmp_root = ws / ".tmp"
        if os.path.exists(win_long_path(tmp_root)):
            for b_dir in tmp_root.iterdir():
                if b_dir.is_dir() and os.path.exists(win_long_path(b_dir / chapter_name / "manifest.json")):
                    tmp_dir = b_dir / chapter_name
                    if not book_name:
                        book_name = b_dir.name
                    break

    if not tmp_dir or not os.path.exists(win_long_path(tmp_dir / "manifest.json")):
        print(f"Error: Manifest not found for chapter '{chapter_name}' in .tmp. Run preprocess_minerU.py first.")
        return False

    manifest_file = tmp_dir / "manifest.json"
    with open(win_long_path(manifest_file), "r", encoding="utf-8") as f:
        manifest = json.load(f)

    if not book_name:
        book_name = manifest.get("book_name", "Book")

    total_chunks = manifest.get("total_chunks", 0)
    chunks_info = manifest.get("chunks", [])

    print(f"=== Assembling Chapter: {chapter_name} ({book_name}) ===")
    print(f"Total chunks: {total_chunks}")

    assembled_content = []
    missing_chunks = []

    for item in chunks_info:
        idx = item["index"]
        ita_chunk_name = f"chunk_{idx:03d}_ita.md"
        raw_chunk_name = f"chunk_{idx:03d}.md"
        ita_chunk_path = tmp_dir / ita_chunk_name
        raw_chunk_path = tmp_dir / raw_chunk_name

        if os.path.exists(win_long_path(ita_chunk_path)):
            with open(win_long_path(ita_chunk_path), "r", encoding="utf-8") as f:
                assembled_content.append(f.read().rstrip() + "\n\n")
        elif allow_partial and os.path.exists(win_long_path(raw_chunk_path)):
            with open(win_long_path(raw_chunk_path), "r", encoding="utf-8") as f:
                assembled_content.append(f.read().rstrip() + "\n\n")
            missing_chunks.append(ita_chunk_name)
        else:
            missing_chunks.append(ita_chunk_name)

    if missing_chunks and not allow_partial:
        print(f"Warning: {len(missing_chunks)} chunks not translated yet: {missing_chunks[:5]}...")
        return False

    if missing_chunks and allow_partial:
        print(f"Note: Assembling partial draft with {len(missing_chunks)} untranslated chunks included in original language.")

    # Target directory in output/<Book>/<Chapter>/
    target_dir = ws / "output" / book_name / chapter_name
    os.makedirs(win_long_path(target_dir), exist_ok=True)
    output_file = target_dir / f"{chapter_name}.md"

    final_text = "".join(assembled_content).strip() + "\n"

    with open(win_long_path(output_file), "w", encoding="utf-8") as f:
        f.write(final_text)

    # Deliverable rule audit: Ensure only <Chapter>.md and images/ exist in target_dir
    allowed = {f"{chapter_name}.md", "images"}
    current_files = set(os.listdir(win_long_path(target_dir)))
    extraneous = current_files - allowed
    if extraneous:
        print(f"Warning: Found extraneous files in deliverable directory: {extraneous}")
        for ext_f in extraneous:
            ext_path = target_dir / ext_f
            ext_path_long = win_long_path(ext_path)
            if os.path.isfile(ext_path_long):
                os.unlink(ext_path_long)
            elif os.path.isdir(ext_path_long):
                import shutil
                shutil.rmtree(ext_path_long)
            print(f"Cleaned up extraneous file: {ext_f}")

    print(f"Successfully assembled deliverable: {output_file}")
    print(f"Total lines: {len(final_text.splitlines())}, Total characters: {len(final_text)}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Assemble translated chunks into output/<Book>/<Chapter>/<Chapter>.md")
    parser.add_argument("--chapter", required=True, help="Chapter folder name")
    parser.add_argument("--book", default=None, help="Book folder name")
    parser.add_argument("--workspace", default=".", help="Workspace root directory")
    parser.add_argument("--allow-partial", action="store_true", help="Assemble partial draft using original chunks for untranslated ones")
    args = parser.parse_args()

    success = assemble_chapter(args.chapter, args.book, args.workspace, args.allow_partial)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
