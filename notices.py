"""Restricted rich-text notices; never trust editor HTML."""
from html import escape
from html.parser import HTMLParser
from markupsafe import Markup
from pathlib import Path
from urllib.parse import urlsplit
from markdown_it import MarkdownIt

MARKDOWN = MarkdownIt('js-default', {'html': False, 'breaks': True})

ALLOWED = {'a', 'h1', 'h4', 'h5', 'h6', 'pre', 'code', 'hr', 's', 'table', 'thead', 'tbody', 'tr', 'th', 'td', 'p', 'div', 'br', 'h2', 'h3', 'strong', 'b', 'em', 'i', 'u', 'ul', 'ol', 'li', 'blockquote'}

class NoticeParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.stack = []
        self.text = []

    def handle_starttag(self, tag, attrs):
        if tag in ALLOWED:
            attributes = ''
            if tag == 'a':
                href = dict(attrs).get('href', '')
                try:
                    safe = (href and not any(ord(char) < 33 for char in href) and '\\' not in href
                            and not href.startswith('//') and urlsplit(href).scheme.lower() in ('', 'http', 'https', 'mailto'))
                except ValueError:
                    safe = False
                if safe:
                    attributes = f' href="{escape(href, quote=True)}" rel="noopener noreferrer"'
            self.parts.append(f'<{tag}{attributes}>')
            if tag not in ('br', 'hr'):
                self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in self.stack:
            while self.stack:
                current = self.stack.pop()
                self.parts.append(f'</{current}>')
                if current == tag:
                    break

    def handle_data(self, data):
        self.parts.append(escape(data))
        self.text.append(data)


def sanitize_notice(value):
    parser = NoticeParser()
    parser.feed(value)
    parser.close()
    for tag in reversed(parser.stack):
        parser.parts.append(f'</{tag}>')
    return ''.join(parser.parts) if ''.join(parser.text).strip() else ''


def display_notice(value, rich=False):
    return Markup(sanitize_notice(value if rich else MARKDOWN.render(value)))


def example_notice(kind, language="en"):
    return Markup(sanitize_notice((Path(__file__).parent / 'data' / f'{kind}_example_{language}.html').read_text()))
