#!/usr/bin/env python3
"""Пересобирает список книг в README.md из frontmatter файлов books/*.md."""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOOKS = ROOT / "books"
ASSETS = BOOKS / "_assets"
README = ROOT / "README.md"
START, END = "<!-- index:start -->", "<!-- index:end -->"
COVER_HEIGHT = 220


def parse_page(text):
    """Метаданные берутся из шапки конспекта: заголовок, строка автора и строка оригинала.

    YAML-frontmatter не используется намеренно: GitHub рендерит его таблицей
    поверх страницы книги.
    """
    title = re.search(r"^# (.+)$", text, re.M)
    meta = re.search(r"^\*\*(?P<author>[^*]+)\*\*\s*·\s*(?P<year>\d{4})(?P<rest>.*)$", text, re.M)
    if not title or not meta:
        return None
    orig = re.search(r"<sub>Оригинал:\s*\*(?P<title>[^*]+)\*(?:,\s*(?P<author>[^·<]+))?", text)
    return {
        "name": title.group(1).strip(),
        "author": meta.group("author").strip(),
        "year": meta.group("year"),
        "tags": re.findall(r"`([^`]+)`", meta.group("rest")),
        "orig_title": orig.group("title").strip() if orig else None,
        "orig_author": (orig.group("author") or "").strip() if orig else None,
    }


def cover(path):
    png = ASSETS / path.stem / "cover.png"
    return png if png.exists() else None


def shelf(books):
    """Ряд обложек-ссылок: по обложке книга узнаётся раньше, чем прочитано название."""
    covers = [(p, m) for p, m in books if cover(p)]
    if not covers:
        return []
    rows = ["<p>"]
    for path, meta in covers:
        rows.append(
            '  <a href="books/{name}"><img src="books/_assets/{slug}/cover.png"'
            ' height="{h}" alt="{alt}"></a>'.format(
                name=path.name, slug=path.stem, h=COVER_HEIGHT,
                alt=meta["name"].replace('"', "'"),
            )
        )
    rows.append("</p>")
    return rows


def card(path, meta):
    head = ["**{}**".format(meta["author"]), meta["year"]]
    if meta["tags"]:
        head.append(" ".join("`{}`".format(t) for t in meta["tags"]))
    lines = ["### [{}](books/{})".format(meta["name"], path.name), "", " · ".join(head)]
    if meta["orig_title"]:
        orig = "Оригинал: *{}*".format(meta["orig_title"])
        if meta["orig_author"]:
            orig += ", {}".format(meta["orig_author"])
        lines += ["", "<sub>{}</sub>".format(orig)]
    return lines


def main():
    books = []
    for path in sorted(BOOKS.glob("*.md")):
        meta = parse_page(path.read_text(encoding="utf-8"))
        if meta is None:
            print("пропускаю {}: не разобрал шапку".format(path.name), file=sys.stderr)
            continue
        books.append((path, meta))
    books.sort(key=lambda b: b[1]["name"].lower())

    block = shelf(books)
    for path, meta in books:
        block += [""] + card(path, meta)

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
