#!/usr/bin/env python3
"""
Validation script for translated scientific markdown files:
- Checks LaTeX math delimiter parity ($$ and $).
- Verifies image link paths and file existence on disk in output/<Book>/<Chapter>/images/.
- Verifies code block syntax and closures.
- Audits deliverable folder compliance (only <Chapter>.md and images/ allowed).
- Compares against original file in input/ if provided.
"""

import os
import sys
import re
import argparse
from pathlib import Path


def win_long_path(p):
    p_str = str(Path(p).resolve())
    if os.name == 'nt' and not p_str.startswith('\\\\?\\'):
        return '\\\\?\\' + p_str
    return p_str


def validate_markdown(file_path, original_path=None, images_dir=None):
    file_path = Path(file_path).resolve()
    if not os.path.exists(win_long_path(file_path)):
        print(f"Error: File not found: {file_path}")
        return False

    print(f"=== Validating Deliverable: {file_path.name} ===")

    with open(win_long_path(file_path), "r", encoding="utf-8") as f:
        text = f.read()

    errors = []
    warnings = []

    # 1. LaTeX Display Math Check ($$...$$)
    display_math_delimiters = text.count("$$")
    if display_math_delimiters % 2 != 0:
        errors.append(f"Unmatched display math delimiter '$$' (count: {display_math_delimiters})")
    
    # 2. LaTeX Inline Math Check
    text_without_display = re.sub(r"\$\$.*?\$\$", "", text, flags=re.DOTALL)
    text_without_code = re.sub(r"```.*?```", "", text_without_display, flags=re.DOTALL)
    
    inline_dollar_count = text_without_code.count("$")
    if inline_dollar_count % 2 != 0:
        warnings.append(f"Odd number of single '$' delimiters ({inline_dollar_count}). Check for unclosed inline math.")

    # 3. Code Blocks Check
    code_backticks = re.findall(r"^```", text, flags=re.MULTILINE)
    if len(code_backticks) % 2 != 0:
        errors.append(f"Unmatched code block delimiter '```' (count: {len(code_backticks)})")

    # 4. Image References and File Existence Check
    images = re.findall(r"!\[(.*?)\]\((images/[^)]+)\)", text)
    missing_images = []
    
    # Determine base directory for resolving relative image paths
    if images_dir:
        img_base = Path(images_dir).resolve()
    else:
        img_base = file_path.parent

    for caption, img_rel_path in images:
        clean_rel_path = img_rel_path.strip().split()[0]
        full_img_path = img_base / clean_rel_path
        if not os.path.exists(win_long_path(full_img_path)):
            if os.path.exists(win_long_path(img_base / "images" / Path(clean_rel_path).name)):
                pass
            elif os.path.exists(win_long_path(img_base / Path(clean_rel_path).name)):
                pass
            else:
                missing_images.append(clean_rel_path)

    if missing_images:
        errors.append(f"{len(missing_images)} referenced image(s) not found on disk: {missing_images[:3]}")

    # 5. Deliverable Rule Audit
    parent_dir = file_path.parent
    allowed = {file_path.name, "images"}
    actual = set(os.listdir(win_long_path(parent_dir)))
    extraneous = actual - allowed
    if extraneous:
        errors.append(f"Deliverable directory contains unauthorized files/folders: {extraneous}")

    # 6. Comparison with Original (if provided)
    if original_path:
        orig_p = Path(original_path).resolve()
        if os.path.exists(win_long_path(orig_p)):
            with open(win_long_path(orig_p), "r", encoding="utf-8") as f:
                orig_text = f.read()

            orig_math_blocks = len(re.findall(r"\$\$.*?\$\$", orig_text, flags=re.DOTALL))
            curr_math_blocks = len(re.findall(r"\$\$.*?\$\$", text, flags=re.DOTALL))
            orig_images = len(re.findall(r"!\[.*?\]\(.*?\)", orig_text))
            curr_images = len(images)

            print(f"Comparison with original:")
            print(f"  - Math blocks: Translated = {curr_math_blocks}, Original = {orig_math_blocks}")
            print(f"  - Images: Translated = {curr_images}, Original = {orig_images}")

            if orig_math_blocks > 0 and curr_math_blocks < orig_math_blocks * 0.90:
                warnings.append(f"Math block count decreased ({curr_math_blocks} vs {orig_math_blocks})")
            if curr_images < orig_images:
                warnings.append(f"Image count decreased ({curr_images} vs {orig_images})")

    # Summary
    print("-" * 40)
    if not errors and not warnings:
        print(" [PASS] All deliverable checks passed cleanly!")
        return True
    
    if warnings:
        print(f" [WARNINGS] ({len(warnings)}):")
        for w in warnings:
            print(f"   - {w}")

    if errors:
        print(f" [FAIL] ({len(errors)} errors):")
        for e in errors:
            print(f"   - {e}")
        return False

    print(" [PASS WITH WARNINGS] No fatal errors.")
    return True


def main():
    parser = argparse.ArgumentParser(description="Validate translated markdown deliverable in output/.")
    parser.add_argument("--file", required=True, help="Path to translated markdown file in output/")
    parser.add_argument("--original", default=None, help="Optional path to original markdown file in input/")
    parser.add_argument("--images-dir", default=None, help="Optional path to folder containing images")
    args = parser.parse_args()

    success = validate_markdown(args.file, args.original, args.images_dir)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
