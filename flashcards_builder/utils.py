from __future__ import annotations

import re
import unicodedata
from pathlib import Path


MULTISPACE_RE = re.compile(r"\s+")


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    lowered = ascii_only.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return slug or "document"


def clean_text(value: str) -> str:
    value = value.replace("\u00a0", " ")
    value = value.replace("\uf0ca", " ")
    value = value.replace("\uf0c9", " ")
    value = value.replace("\u2019", "'")
    value = value.replace("\u2018", "'")
    value = value.replace("\u201c", '"')
    value = value.replace("\u201d", '"')
    value = value.replace("\ufb01", "fi")
    value = value.replace("\ufb02", "fl")
    return value.strip()


def normalize_inline_whitespace(value: str) -> str:
    return MULTISPACE_RE.sub(" ", clean_text(value)).strip()


def ensure_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def humanize_pdf_title(value: str) -> str:
    text = value.strip()
    text = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", text)
    text = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", text)
    text = re.sub(r"(?<=[A-Za-z])(?=[0-9]+$)", " ", text)

    match = re.search(r"(\d+)$", text)
    if match:
        number = match.group(1)
        text = f"{text[:-len(number)].rstrip()} {number}%"

    text = re.sub(r"\s+", " ", text).strip()
    return text or value
