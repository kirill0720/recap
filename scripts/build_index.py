#!/usr/bin/env python3
"""Пересобирает таблицу книг в README.md из frontmatter файлов books/*.md."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOOKS = ROOT / "books"
ASSETS = BOOKS / "_assets"
README = ROOT / "README.md"
START, END = "<!-- index:start -->", "<!-- index:end -->"


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


def row(path, fm):
    slug = path.stem
    cover = ASSETS / slug / "cover.png"
    thumb = (
        f'<img src="books/_assets/{slug}/cover.png" width="60">' if cover.exists() else ""
    )
    name = fm.get("title_ru") or fm.get("title") or slug
    tags = fm.get("tags") or []
    if isinstance(tags, str):
        tags = [tags]
    return "| {} | [{}](books/{}) | {} | {} | {} |".format(
        thumb,
        name,
        path.name,
        fm.get("author") or "—",
        fm.get("year") or "—",
        ", ".join(tags) or "—",
    )


def main():
    books = []
    for path in sorted(BOOKS.glob("*.md")):
        fm = parse_frontmatter(path.read_text(encoding="utf-8"))
        if fm is None:
            print(f"пропускаю {path.name}: нет frontmatter", file=sys.stderr)
            continue
        books.append((path, fm))

    books.sort(key=lambda b: (b[1].get("title_ru") or b[1].get("title") or b[0].stem).lower())

    lines = [
        "|  | Книга | Автор | Год | Теги |",
        "|---|---|---|---|---|",
    ]
    lines += [row(p, fm) for p, fm in books]
    table = "\n".join(lines)

    text = README.read_text(encoding="utf-8")
    head, sep, rest = text.partition(START)
    if not sep:
        sys.exit(f"в README.md нет маркера {START}")
    _, sep, tail = rest.partition(END)
    if not sep:
        sys.exit(f"в README.md нет маркера {END}")
    README.write_text(f"{head}{START}\n\n{table}\n\n{END}{tail}", encoding="utf-8")

    with_cover = sum(1 for p, _ in books if (ASSETS / p.stem / "cover.png").exists())
    print(f"README.md обновлён. Книг: {len(books)}, с обложкой: {with_cover}")


if __name__ == "__main__":
    main()
