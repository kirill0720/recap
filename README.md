# recap

Краткие содержания прочитанных книг. Пишет Claude, чтобы можно было за несколько минут освежить книгу в памяти: термины, ключевые идеи, примеры и схемы из оригинала.

## Книги

<!-- index:start -->

|  | Книга | Автор | Год | Яз. | Читал | Теги |
|---|---|---|---|---|---|---|
| <img src="books/_assets/learning-ddd-khononov/cover.png" width="60"> | [Изучаем DDD — предметно-ориентированное проектирование](books/learning-ddd-khononov.md) | Влад Хононов | 2022 | ru | 2026-09 | ddd, architecture, design, microservices |

<!-- index:end -->

## Как добавить книгу

1. `cp TEMPLATE.md books/<slug>.md` и заполнить frontmatter.
2. Обложка: `pdftoppm -png -r 60 -f 1 -l 1 -singlefile <pdf> books/_assets/<slug>/cover`
3. Попросить Claude написать конспект — правила в [CLAUDE.md](CLAUDE.md).
4. `python3 scripts/build_index.py` — пересоберёт таблицу выше.

Нужен poppler: `brew install poppler`.
