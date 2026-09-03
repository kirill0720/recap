#!/usr/bin/env python3
"""Пересобирает список книг в README.md из frontmatter файлов books/*.md."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOOKS = ROOT / "books"
ASSETS = BOOKS / "_assets"
README = ROOT / "README.md"
START, END = "<!-- index:start -->", "<!-- index:end -->"
COVER_HEIGHT = 220


def parse_frontmatter(text):
    if not text.startswith("---"):
        return None
    _, _, rest = text.partition("\n")
    body, sep, _ = rest.partition("\n---")
    if not sep:
        return None
    data = {}
    for line in body.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, sep, value = line.partition(":")
        if not sep:
            continue
        value = value.split("  #")[0].strip()
        if value.startswith("[") and value.endswith("]"):
            value = [v.strip() for v in value[1:-1].split(",") if v.strip()]
        data[key.strip()] = value
    return data


def display_name(path, fm):
    return fm.get("title_ru") or fm.get("title") or path.stem


def cover(path):
    png = ASSETS / path.stem / "cover.png"
    return png if png.exists() else None


def shelf(books):
    """Ряд обложек-ссылок: с ним книга узнаётся раньше, чем прочитано название."""
    covers = [(p, fm) for p, fm in books if cover(p)]
    if not covers:
        return []
    rows = ["<p>"]
    for path, fm in covers:
        rows.append(
            '  <a href="books/{name}"><img src="books/_assets/{slug}/cover.png"'
            ' height="{h}" alt="{alt}"></a>'.format(
                name=path.name, slug=path.stem, h=COVER_HEIGHT,
                alt=display_name(path, fm).replace('"', "'"),
            )
        )
    rows.append("</p>")
    return rows


def card(path, fm):
    name = display_name(path, fm)
    author = fm.get("author_ru") or fm.get("author")
    tags = fm.get("tags") or []
    if isinstance(tags, str):
        tags = [tags]

    meta = [x for x in ("**{}**".format(author) if author else "", str(fm.get("year") or "")) if x]
    meta += [" ".join("`{}`".format(t) for t in tags)] if tags else []

    lines = ["### [{}](books/{})".format(name, path.name), ""]
    if meta:
        lines += [" · ".join(meta)]
    if fm.get("title_ru") and fm.get("title"):
        orig = "Оригинал: *{}*".format(fm["title"])
        if fm.get("author"):
            orig += ", {}".format(fm["author"])
        lines += ["", "<sub>{}</sub>".format(orig)]
    return lines


def main():
    books = []
    for path in sorted(BOOKS.glob("*.md")):
        fm = parse_frontmatter(path.read_text(encoding="utf-8"))
        if fm is None:
            print("пропускаю {}: нет frontmatter".format(path.name), file=sys.stderr)
            continue
        books.append((path, fm))
    books.sort(key=lambda b: display_name(*b).lower())

    block = shelf(books)
    for path, fm in books:
        block += [""] + card(path, fm)

    text = README.read_text(encoding="utf-8")
    head, sep, rest = text.partition(START)
    if not sep:
        sys.exit("в README.md нет маркера {}".format(START))
    _, sep, tail = rest.partition(END)
    if not sep:
        sys.exit("в README.md нет маркера {}".format(END))
    README.write_text(
        "{}{}\n\n{}\n\n{}{}".format(head, START, "\n".join(block).strip("\n"), END, tail),
        encoding="utf-8",
    )
    print("README.md обновлён. Книг: {}, с обложкой: {}".format(
        len(books), sum(1 for p, _ in books if cover(p))))


if __name__ == "__main__":
    main()
