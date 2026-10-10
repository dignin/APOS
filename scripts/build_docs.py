"""Render the tracked Markdown guides as static GitHub Pages documentation.

Run from any directory with a Python environment containing markdown-it-py.
The Markdown files remain the source of truth; generated HTML is not committed.
"""

from html import escape
import os
from pathlib import Path
from urllib.parse import urlsplit

from markdown_it import MarkdownIt


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
OUTPUT = ROOT / "site" / "docs"
SOURCES = [DOCS / "README.md"]
SOURCES += [DOCS / lang / f"{role}.md" for lang in ("en", "de") for role in ("STAFF", "GUEST", "ADMIN")]
SOURCES += [DOCS / name for name in ("COMPLIANCE.md", "OPERATIONS.md", "SPECIFICATION.md")]
DESTINATIONS = {
    source.resolve(): OUTPUT / ("index.html" if source.name == "README.md" else source.relative_to(DOCS).with_suffix(".html"))
    for source in SOURCES
}


def render(source: Path) -> None:
    destination = DESTINATIONS[source.resolve()]
    markdown = MarkdownIt("commonmark", {"html": False}).enable("table")
    tokens = markdown.parse(source.read_text(encoding="utf-8"))
    for token in tokens:
        for child in token.children or []:
            if child.type != "link_open":
                continue
            href = child.attrGet("href")
            parsed = urlsplit(href)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            target = (source.parent / parsed.path).resolve()
            if not target.is_relative_to(ROOT) or not target.is_file():
                raise ValueError(f"Missing or unsafe documentation link in {source}: {href}")
            if target in DESTINATIONS:
                url = Path(os.path.relpath(DESTINATIONS[target], destination.parent)).as_posix()
            else:
                url = "https://github.com/dignin/APOS/blob/main/" + target.relative_to(ROOT).as_posix()
            if parsed.fragment:
                url += "#" + parsed.fragment
            child.attrSet("href", url)
    body = markdown.renderer.render(tokens, markdown.options, {})
    title = source.read_text(encoding="utf-8").splitlines()[0].removeprefix("# ")
    language = "de" if source.parent.name == "de" else "en"
    home = Path(os.path.relpath(ROOT / "site" / "index.html", destination.parent)).as_posix()
    index = Path(os.path.relpath(OUTPUT / "index.html", destination.parent)).as_posix()
    stylesheet = Path(os.path.relpath(OUTPUT / "docs.css", destination.parent)).as_posix()
    skip = "Zum Inhalt springen" if language == "de" else "Skip to content"
    label = "Dokumentation" if language == "de" else "Documentation"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(f'''<!doctype html>
<html lang="{language}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)} — APOS</title><link rel="stylesheet" href="{stylesheet}"></head>
<body><a class="skip" href="#main">{skip}</a>
<header><a href="{home}">APOS</a><nav aria-label="{label}"><a href="{index}">{label}</a>
<a href="https://github.com/dignin/APOS">GitHub ↗</a></nav></header>
<main id="main">{body}</main>
<footer><a href="{index}">{label}</a> · APOS 0.6</footer></body></html>
''', encoding="utf-8")


if __name__ == "__main__":
    for source in SOURCES:
        render(source)
    print(f"Rendered {len(SOURCES)} documentation pages.")
