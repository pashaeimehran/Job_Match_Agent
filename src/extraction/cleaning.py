from __future__ import annotations

import html
import re
from html.parser import HTMLParser


BOILERPLATE_LINES = {
    "apply now",
    "jetzt bewerben",
    "bewerben sie sich jetzt",
    "save job",
    "share job",
    "cookie settings",
    "datenschutzeinstellungen",
}


class _TextExtractor(HTMLParser):
    BLOCK_TAGS = {
        "br",
        "p",
        "div",
        "li",
        "ul",
        "ol",
        "section",
        "article",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def text(self) -> str:
        return "".join(self.parts)


def clean_job_text(raw_text: str) -> str:
    """Normalize HTML/whitespace and remove a few exact UI boilerplate lines."""

    if not isinstance(raw_text, str):
        raise TypeError("raw_text must be a string")

    parser = _TextExtractor()
    parser.feed(raw_text)
    parser.close()

    text = html.unescape(parser.text())
    text = text.replace("\u200b", "").replace("\xa0", " ")
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    cleaned_lines: list[str] = []
    for line in text.split("\n"):
        line = re.sub(r"[\t ]+", " ", line).strip()
        if not line:
            cleaned_lines.append("")
            continue
        if line.casefold() in BOILERPLATE_LINES:
            continue
        cleaned_lines.append(line)

    cleaned = "\n".join(cleaned_lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()
