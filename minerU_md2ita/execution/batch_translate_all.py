#!/usr/bin/env python3
"""
Batch Translation Orchestrator for all MinerU Books and Chapters.
Executes high-fidelity Italian translation for every chapter across all books,
assembles final clean deliverables, and performs deterministic validation.
"""

import os
import sys
import time
from pathlib import Path

# Ensure repo root in sys.path
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from execution.translate_engine import translate_chapter, win_long_path


def batch_translate(workspace_root=".", workers_per_chapter=8, max_chapters=None):
    ws = Path(workspace_root).resolve()
    tmp_dir = ws / ".tmp"

    books = [
        "Applied_Digital_Signal_Processing_Theory_and_Practice",
        "Digital_Signal_Processing_-_Principles,_Algorithms,_and_Applications",
        "FPGA-based_Implementation_of_Signal_Processing_Systems"
    ]

    total_chapters_processed = 0
    success_chapters = 0
    failed_chapters = []

    start_time = time.time()

    for book in books:
        book_dir = tmp_dir / book
        if not os.path.exists(win_long_path(book_dir)):
            print(f"Warning: Book dir not found: {book_dir}", flush=True)
            continue

        chapters = sorted([c for c in book_dir.iterdir() if c.is_dir() and os.path.exists(win_long_path(c / "manifest.json"))])
        print(f"\n=======================================================", flush=True)
        print(f"=== BATCH TRANSLATING BOOK: {book} ({len(chapters)} chapters) ===", flush=True)
        print(f"=======================================================\n", flush=True)

        for c_idx, chap in enumerate(chapters, 1):
            if max_chapters and total_chapters_processed >= max_chapters:
                break

            total_chapters_processed += 1
            chap_name = chap.name
            print(f"\n>>> [{c_idx}/{len(chapters)}] Starting: {chap_name} (Book: {book})", flush=True)
            t0 = time.time()
            
            try:
                ok = translate_chapter(chap_name, book_name=book, workspace_root=workspace_root, max_workers=workers_per_chapter)
                elapsed = time.time() - t0
                if ok:
                    success_chapters += 1
                    print(f">>> [SUCCESS] {chap_name} completed in {elapsed:.1f}s", flush=True)
                else:
                    failed_chapters.append((book, chap_name))
                    print(f">>> [WARNING] {chap_name} finished with validation issues in {elapsed:.1f}s", flush=True)
            except Exception as e:
                elapsed = time.time() - t0
                failed_chapters.append((book, chap_name))
                print(f">>> [ERROR] {chap_name} failed: {e} in {elapsed:.1f}s", flush=True)

    total_elapsed = time.time() - start_time
    print(f"\n=======================================================", flush=True)
    print(f"=== BATCH TRANSLATION COMPLETE ===", flush=True)
    print(f"Total Chapters Processed: {total_chapters_processed}", flush=True)
    print(f"Successfully Validated: {success_chapters}", flush=True)
    print(f"Failed / Issues: {len(failed_chapters)}", flush=True)
    if failed_chapters:
        print("Chapters with issues:", flush=True)
        for b, ch in failed_chapters:
            print(f"  - {b} -> {ch}", flush=True)
    print(f"Total Time: {total_elapsed/60:.2f} minutes", flush=True)
    print(f"=======================================================\n", flush=True)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Batch translate all chapters across all books.")
    parser.add_argument("--workspace", default=".", help="Workspace root directory")
    parser.add_argument("--workers", type=int, default=8, help="Workers per chapter")
    parser.add_argument("--max-chapters", type=int, default=None, help="Optional limit for testing")
    args = parser.parse_args()

    batch_translate(args.workspace, args.workers, args.max_chapters)
