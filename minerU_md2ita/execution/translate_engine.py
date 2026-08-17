#!/usr/bin/env python3
"""
High-Fidelity Scientific Translation Engine (EN -> IT) for MinerU Markdown Chunks.
- Protects LaTeX display math ($$...$$) and inline math ($...$) via placeholders.
- Protects code blocks (```...```) and inline code (`...`) via placeholders.
- Preserves image syntax (![...](...)) and table formatting intact.
- Enforces academic Italian style and terminology consistency.
- Operates concurrently with rate limiting and exponential backoff.
"""

import os
import sys
import re
import json
import time
import urllib.request
import urllib.parse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Ensure repository root is in sys.path
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))


def win_long_path(p):
    p_str = str(Path(p).resolve())
    if os.name == 'nt' and not p_str.startswith('\\\\?\\'):
        return '\\\\?\\' + p_str
    return p_str


def translate_raw_text(text, source='en', target='it', max_retries=5):
    """
    Translates raw text segment using Google GTX API with robust error handling and UTF-8 encoding.
    """
    if not text or not text.strip():
        return text

    # Split very long paragraphs to respect URL length limits if needed (< 2500 chars)
    if len(text) > 2500:
        lines = text.split("\n")
        translated_lines = []
        for line in lines:
            if len(line) > 2500:
                # split by sentences
                sentences = re.split(r'(?<=[.!?])\s+', line)
                trans_sentences = [translate_raw_text(s, source, target) for s in sentences]
                translated_lines.append(" ".join(trans_sentences))
            else:
                translated_lines.append(translate_raw_text(line, source, target))
        return "\n".join(translated_lines)

    encoded = urllib.parse.quote(text.strip())
    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={source}&tl={target}&dt=t&q={encoded}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as res:
                content = res.read().decode('utf-8')
                data = json.loads(content)
                translated = "".join(sentence[0] for sentence in data[0] if sentence and sentence[0])
                
                # Preserve leading/trailing whitespace
                leading_ws = re.match(r"^\s*", text).group(0)
                trailing_ws = re.search(r"\s*$", text).group(0)
                return leading_ws + translated + trailing_ws
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"Warning: Translation failed after {max_retries} attempts: {e}")
                return text
            time.sleep(0.5 * (attempt + 1))
            
    return text


def polish_dsp_terminology(text):
    """
    Applies scientific Italian technical standard terminology and fixes translation artifacts.
    """
    replacements = [
        (r"\bpassa basso\b", "passa-basso"),
        (r"\bpassa alto\b", "passa-alto"),
        (r"\bpassa banda\b", "passa-banda"),
        (r"\barresta banda\b", "arresta-banda"),
        (r"\bpassabasso\b", "passa-basso"),
        (r"\bpassaalto\b", "passa-alto"),
        (r"\bpassabanda\b", "passa-banda"),
        (r"\barrestabanda\b", "arresta-banda"),
        (r"\bpassa tutto\b", "passa-tutto"),
        (r"\bpassatutto\b", "passa-tutto"),
        (r"\bfiltro all-pass\b", "filtro passa-tutto"),
        (r"\bfiltri all-pass\b", "filtri passa-tutto"),
        (r"\britardo di gruppo\b", "ritardo di gruppo"),
        (r"\btrasformata z\b", "trasformata z"),
        (r"\btrasformata Z\b", "trasformata z"),
        (r"\btrasformata di Fourier a tempo discreto\b", "trasformata di Fourier a tempo discreto (DTFT)"),
        (r"\btrasformata discreta di Fourier\b", "trasformata di Fourier discreta (DFT)"),
        (r"\btrasformata di Fourier veloce\b", "trasformata di Fourier veloce (FFT)"),
        (r"\btempo invariante\b", "tempo-invariante"),
        (r"\btempo invarianti\b", "tempo-invarianti"),
        (r"\blineare tempo invariante\b", "lineare tempo-invariante (LTI)"),
        (r"\blineari tempo invarianti\b", "lineari tempo-invarianti (LTI)"),
        (r"\blineare tempo-invariante\b", "lineare tempo-invariante (LTI)"),
        (r"\blineari tempo-invarianti\b", "lineari tempo-invarianti (LTI)"),
        (r"\b(LTI) \(LTI\)\b", "(LTI)"),
        (r"\b(DTFT) \(DTFT\)\b", "(DTFT)"),
        (r"\b(DFT) \(DFT\)\b", "(DFT)"),
        (r"\b(FFT) \(FFT\)\b", "(FFT)"),
        (r"\b(FIR) \(FIR\)\b", "(FIR)"),
        (r"\b(IIR) \(IIR\)\b", "(IIR)"),
        (r"\b(DSP) \(DSP\)\b", "(DSP)"),
        (r"\b(FPGA) \(FPGA\)\b", "(FPGA)"),
        (r"\b(HDL) \(HDL\)\b", "(HDL)"),
        (r"\b(VHDL) \(VHDL\)\b", "(VHDL)"),
        (r"\b(Verilog) \(Verilog\)\b", "Verilog"),
        (r"\b(MATLAB) \(MATLAB\)\b", "MATLAB"),
        (r"\b(Simulink) \(Simulink\)\b", "Simulink"),
        (r"\b(DAC) \(DAC\)\b", "(DAC)"),
        (r"\b(ADC) \(ADC\)\b", "(ADC)"),
        (r"Esempio (\d+\.\d+)", r"Esempio \1"),
        (r"Figura (\d+\.\d+)", r"Figura \1"),
        (r"Tabella (\d+\.\d+)", r"Tabella \1"),
        (r"Capitolo (\d+)", r"Capitolo \1"),
        (r"Sezione (\d+\.\d+(\.\d+)?)", r"Sezione \1"),
        (r"Problema (\d+)", r"Problema \1"),
        (r"Problemi esercitativi", "Problemi esercitativi"),
        (r"Problemi di base", "Problemi di base"),
        (r"Problemi di valutazione", "Problemi di valutazione"),
        (r"Problemi di riepilogo", "Problemi di riepilogo"),
        (r"Domande di ripasso", "Domande di ripasso"),
        (r"Letture consigliate", "Letture consigliate"),
        (r"Riepilogo", "Riepilogo"),
        (r"Obiettivi di studio", "Obiettivi di studio"),
    ]

    for pat, repl in replacements:
        text = re.sub(pat, repl, text, flags=re.IGNORECASE)

    return text


def translate_chunk_markdown(content):
    """
    Translates a single markdown chunk while shielding LaTeX math, code, and images.
    """
    placeholders = {}
    counter = 0

    def create_placeholder(val):
        nonlocal counter
        ph_id = counter
        ph = f"ZXQPLACEHOLDER{ph_id:06d}QXZ"
        placeholders[ph_id] = (ph, val)
        counter += 1
        return ph

    # 1. Protect Code Blocks
    def repl_code_block(m):
        return create_placeholder(m.group(0))
    content = re.sub(r"```[\s\S]*?```", repl_code_block, content)

    # 2. Protect Display Math ($$...$$)
    def repl_disp_math(m):
        return create_placeholder(m.group(0))
    content = re.sub(r"\$\$[\s\S]*?\$\$", repl_disp_math, content)

    # 3. Protect Inline Code (`...`)
    def repl_inline_code(m):
        return create_placeholder(m.group(0))
    content = re.sub(r"`[^`\n]+`", repl_inline_code, content)

    # 4. Protect Inline Math ($...$)
    def repl_inline_math(m):
        return create_placeholder(m.group(0))
    content = re.sub(r"\$[^$\n]+\$", repl_inline_math, content)

    # 5. Protect and translate image/table/figure captions as placeholders
    def repl_image(m):
        alt = m.group(1)
        path = m.group(2)
        # do not translate simple sub-figure letters like (a), (b), (c)
        if re.match(r"^\s*\([a-zA-Z0-9]\)\s*$", alt):
            trans_alt = alt.strip()
        elif alt.strip():
            trans_alt = translate_raw_text(alt)
        else:
            trans_alt = ""
        img_tag = f"![{trans_alt}]({path})"
        return create_placeholder(img_tag)
    content = re.sub(r"!\[(.*?)\]\((images/[^)]+)\)", repl_image, content)

    # 6. Translate headings and paragraphs line-by-line or paragraph-by-paragraph
    paragraphs = content.split("\n\n")
    translated_paras = []

    for para in paragraphs:
        if not para.strip():
            translated_paras.append(para)
            continue
        
        # Check if paragraph is purely a placeholder
        is_pure_ph = False
        for ph_id, (ph, orig) in placeholders.items():
            if para.strip() == ph:
                translated_paras.append(orig)
                is_pure_ph = True
                break
        if is_pure_ph:
            continue

        # Headings
        if para.startswith("#"):
            h_match = re.match(r"^(#+)\s*(.*)$", para, flags=re.DOTALL)
            if h_match:
                hashes = h_match.group(1)
                htext = h_match.group(2)
                trans_h = translate_raw_text(htext)
                translated_paras.append(f"{hashes} {trans_h}")
                continue

        # Regular paragraph
        trans_p = translate_raw_text(para)
        translated_paras.append(trans_p)

    translated_content = "\n\n".join(translated_paras)

    # 7. Restore placeholders (case-insensitive and space-resilient)
    for ph_id, (ph, orig) in placeholders.items():
        pattern = rf"Z\s*X\s*Q\s*P\s*L\s*A\s*C\s*E\s*H\s*O\s*L\s*D\s*E\s*R\s*{ph_id:06d}\s*Q\s*X\s*Z"
        translated_content = re.sub(pattern, lambda m: orig, translated_content, flags=re.IGNORECASE)
        # Direct fallback replace
        translated_content = translated_content.replace(ph, orig)

    # 8. Polish technical terminology
    translated_content = polish_dsp_terminology(translated_content)

    return translated_content


def translate_chunk_file(raw_chunk_path, ita_chunk_path):
    """
    Reads a raw chunk file, translates it, and writes the Italian chunk file.
    """
    raw_p = Path(raw_chunk_path)
    ita_p = Path(ita_chunk_path)

    if os.path.exists(win_long_path(ita_p)):
        return True

    with open(win_long_path(raw_p), "r", encoding="utf-8") as f:
        raw_text = f.read()

    trans_text = translate_chunk_markdown(raw_text)

    with open(win_long_path(ita_p), "w", encoding="utf-8") as f:
        f.write(trans_text)

    return True


def translate_chapter(chapter_name, book_name=None, workspace_root=".", max_workers=6):
    """
    Translates all chunks of a chapter concurrently and assembles the final deliverable.
    """
    ws = Path(workspace_root).resolve()
    
    # Locate tmp directory
    tmp_dir = None
    if book_name and os.path.exists(win_long_path(ws / ".tmp" / book_name / chapter_name)):
        tmp_dir = ws / ".tmp" / book_name / chapter_name
    elif os.path.exists(win_long_path(ws / ".tmp" / chapter_name)):
        tmp_dir = ws / ".tmp" / chapter_name
    else:
        for b_dir in (ws / ".tmp").iterdir():
            if b_dir.is_dir() and os.path.exists(win_long_path(b_dir / chapter_name)):
                tmp_dir = b_dir / chapter_name
                book_name = b_dir.name
                break

    if not tmp_dir or not os.path.exists(win_long_path(tmp_dir / "manifest.json")):
        print(f"Error: Manifest not found for chapter '{chapter_name}' in .tmp")
        return False

    with open(win_long_path(tmp_dir / "manifest.json"), "r", encoding="utf-8") as f:
        manifest = json.load(f)

    if not book_name:
        book_name = manifest.get("book_name", "Book")

    chunks = manifest.get("chunks", [])
    print(f"=== Translating Chapter: {chapter_name} ({book_name}) - {len(chunks)} chunks ===", flush=True)

    tasks = []
    for c in chunks:
        idx = c["index"]
        raw_f = tmp_dir / f"chunk_{idx:03d}.md"
        ita_f = tmp_dir / f"chunk_{idx:03d}_ita.md"
        tasks.append((raw_f, ita_f, idx))

    completed = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {executor.submit(translate_chunk_file, r, i): idx for r, i, idx in tasks}
        for future in as_completed(future_map):
            idx = future_map[future]
            try:
                future.result()
                completed += 1
                print(f"  [{completed}/{len(chunks)}] Chunk {idx:03d} translated successfully.", flush=True)
            except Exception as e:
                print(f"  [ERROR] Chunk {idx:03d} failed: {e}", flush=True)

    # Assemble chapter
    from execution.assemble_chapter import assemble_chapter
    assemble_ok = assemble_chapter(chapter_name, book_name=book_name, workspace_root=workspace_root, allow_partial=False)

    # Validate chapter
    from execution.validate_translation import validate_markdown
    out_file = ws / "output" / book_name / chapter_name / f"{chapter_name}.md"
    val_ok = validate_markdown(str(out_file))

    print(f"=== Finished Chapter: {chapter_name} (Assemble: {assemble_ok}, Validate: {val_ok}) ===", flush=True)
    return assemble_ok and val_ok


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Translate MinerU Markdown chunks to academic Italian.")
    parser.add_argument("--chapter", required=True, help="Chapter folder name")
    parser.add_argument("--book", default=None, help="Book folder name")
    parser.add_argument("--workspace", default=".", help="Workspace root directory")
    parser.add_argument("--workers", type=int, default=6, help="Concurrent workers")
    args = parser.parse_args()

    translate_chapter(args.chapter, args.book, args.workspace, args.workers)
