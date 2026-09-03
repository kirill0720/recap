#!/usr/bin/env python3
"""Вырезает иллюстрации из PDF книги по подписям «Рис. N.M».

В PDF рисунки нарезаны на полоски, поэтому pdfimages бесполезен: скрипт находит
подпись, вычисляет прямоугольник над ней, свободный от текста, и рендерит его.

    scripts/extract_figures.py <pdf> <out_dir> 1.1 3.4 8.2 [--dpi 150]

Требуется poppler (pdftotext, pdfinfo, pdftoppm).
"""

import argparse
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "{http://www.w3.org/1999/xhtml}"
CAPTION = re.compile(r"^Рис\.\s*(\d+\.\d+)")
CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
MIN_GAP_PT = 40.0


def run(*cmd):
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout


def load_pages(pdf):
    """[(page_no, media_h, [(yMin, yMax, xMin, xMax, text), ...]), ...]"""
    xml = run("pdftotext", "-bbox-layout", str(pdf), "-")
    # в тексте попадаются управляющие символы из шрифтов — XML-парсер на них падает
    xml = CONTROL_CHARS.sub("", xml)
    root = ET.fromstring(xml)
    pages = []
    for i, page in enumerate(root.iter(f"{NS}page"), start=1):
        lines = []
        for line in page.iter(f"{NS}line"):
            words = [w.text or "" for w in line.iter(f"{NS}word")]
            lines.append((
                float(line.get("yMin")), float(line.get("yMax")),
                float(line.get("xMin")), float(line.get("xMax")),
                " ".join(words).strip(),
            ))
        pages.append((i, float(page.get("height")), lines))
    return pages


def figure_box(lines, caption_idx):
    """Прямоугольник рисунка: просвет между подписью и ближайшим текстом над ней."""
    caption = lines[caption_idx]
    above = [l for l in lines if l[1] < caption[0]]
    top = min((l[0] for l in lines), default=0.0)
    best_top = max((l[1] for l in above), default=top)
    if caption[0] - best_top < MIN_GAP_PT:
        return None
    body = [l for l in lines if l[4]]
    x_min = min(l[2] for l in body)
    x_max = max(l[3] for l in body)
    return x_min - 6, best_top + 2, x_max + 6, caption[0] - 4


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf", type=Path)
    ap.add_argument("out_dir", type=Path)
    ap.add_argument("figures", nargs="+", help="номера рисунков, например 1.1 3.4")
    ap.add_argument("--dpi", type=int, default=150)
    ap.add_argument("--prefix", default="fig")
    args = ap.parse_args()

    for tool in ("pdftotext", "pdftoppm"):
        if not shutil.which(tool):
            sys.exit(f"нет {tool}: brew install poppler")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    pages = load_pages(args.pdf)

    index = {}
    for page_no, _, lines in pages:
        for i, line in enumerate(lines):
            m = CAPTION.match(line[4])
            if m and m.group(1) not in index:
                index[m.group(1)] = (page_no, lines, i)

    for num in args.figures:
        found = index.get(num)
        if not found:
            print(f"рис. {num}: подпись не найдена", file=sys.stderr)
            continue
        page_no, lines, caption_idx = found
        box = figure_box(lines, caption_idx)
        if not box:
            print(f"рис. {num} (с. {page_no}): не нашёл область над подписью", file=sys.stderr)
            continue
        k = args.dpi / 72.0  # pdftoppm рендерит MediaBox, координаты pdftotext в той же системе
        x = round(box[0] * k)
        y = round(box[1] * k)
        w = round((box[2] - box[0]) * k)
        h = round((box[3] - box[1]) * k)
        out = args.out_dir / f"{args.prefix}-{num.replace('.', '-')}"
        run("pdftoppm", "-png", "-r", str(args.dpi), "-f", str(page_no), "-l", str(page_no),
            "-x", str(max(x, 0)), "-y", str(max(y, 0)), "-W", str(w), "-H", str(h),
            "-singlefile", str(args.pdf), str(out))
        print(f"рис. {num}: с. {page_no}, {w}x{h}px -> {out.name}.png")


if __name__ == "__main__":
    main()
