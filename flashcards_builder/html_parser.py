from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote, urlparse

from bs4 import BeautifulSoup, Tag

from flashcards_builder.models import Flashcard, ImageAsset
from flashcards_builder.pdf_parser import ParseOptions
from flashcards_builder.utils import normalize_inline_whitespace


LABEL_RE = re.compile(r"^([A-Z]):$")
POINTS_RE = re.compile(r"Points:\s*([0-9.]+)\s*/\s*([0-9.]+)", re.IGNORECASE)
USER_ANSWER_RE = re.compile(r"You answered:\s*([A-Z])", re.IGNORECASE)
CORRECT_ANSWER_RE = re.compile(r"Correct answer is:\s*([A-Z])", re.IGNORECASE)


def parse_html_review(html_path: Path, *, options: ParseOptions) -> tuple[list[Flashcard], list[str]]:
    warnings: list[str] = []
    flashcards: list[Flashcard] = []

    try:
        soup = BeautifulSoup(html_path.read_text(encoding="utf-8", errors="ignore"), "html.parser")
    except Exception as exc:
        return [], [f"Failed to read {html_path.name}: {exc}"]

    rows = [row for row in soup.select("div.row.white-row") if row.select_one("#questionText")]
    for row in rows:
        try:
            card = parse_question_row(row, html_path)
        except Exception as exc:
            warnings.append(f"Skipped a malformed question in {html_path.name}: {exc}")
            continue

        if card is None:
            continue
        if options.missed_only and not card.is_missed:
            continue
        flashcards.append(card)

    return flashcards, warnings


def parse_question_row(row: Tag, html_path: Path) -> Flashcard | None:
    question_panel = row.select_one("#questionText")
    if question_panel is None:
        return None

    number_node = question_panel.select_one(".review-question-number")
    if number_node is None:
        return None
    number_text = normalize_inline_whitespace(number_node.get_text(" "))
    number_match = re.search(r"(\d+)", number_text)
    if not number_match:
        return None
    number = int(number_match.group(1))

    question_node = first_question_body(question_panel)
    question = text_from_node(question_node) if question_node else ""
    if not question:
        return None

    points_earned, points_possible = extract_points(question_panel)
    choices = extract_choices(row)
    user_answer, correct_answer_label = extract_answer_labels(row)
    if not correct_answer_label and user_answer:
        correct_answer_label = user_answer

    feedback_node = row.select_one('[data-id="feedback"]')
    feedback = text_from_node(feedback_node) if feedback_node else ""
    answer = resolve_answer(correct_answer_label, choices)
    images = extract_images(row, html_path)

    return Flashcard(
        number=number,
        question=question,
        answer=answer,
        feedback=feedback,
        source_pdf=html_path,
        choices=choices,
        user_answer=user_answer,
        correct_answer_label=correct_answer_label,
        images=images,
        page_numbers=[],
        points_earned=points_earned,
        points_possible=points_possible,
        raw_text=text_from_node(row),
    )


def first_question_body(question_panel: Tag) -> Tag | None:
    for node in question_panel.select(".mce-content-body"):
        if node.get("data-id") == "question-answers":
            continue
        text = text_from_node(node)
        if text:
            return node
    return None


def extract_points(question_panel: Tag) -> tuple[float | None, float | None]:
    points_node = question_panel.select_one(".review-question-points")
    if not points_node:
        return None, None
    match = POINTS_RE.search(points_node.get_text(" "))
    if not match:
        return None, None
    return float(match.group(1)), float(match.group(2))


def extract_choices(row: Tag) -> dict[str, str]:
    choices: dict[str, str] = {}
    for item in row.select("li.list-group-item"):
        label_node = item.find(string=LABEL_RE)
        answer_node = item.select_one('[data-id="question-answers"]')
        if not label_node or answer_node is None:
            continue
        label_match = LABEL_RE.match(label_node.strip())
        if not label_match:
            continue
        choices[label_match.group(1)] = text_from_node(answer_node)
    return choices


def extract_answer_labels(row: Tag) -> tuple[str | None, str | None]:
    blockquote = row.select_one("blockquote")
    text = blockquote.get_text(" ") if blockquote else row.get_text(" ")
    user_match = USER_ANSWER_RE.search(normalize_inline_whitespace(text))
    correct_match = CORRECT_ANSWER_RE.search(normalize_inline_whitespace(text))
    user_answer = user_match.group(1).upper() if user_match else None
    correct_answer = correct_match.group(1).upper() if correct_match else None
    return user_answer, correct_answer


def resolve_answer(correct_answer_label: str | None, choices: dict[str, str]) -> str:
    if correct_answer_label and correct_answer_label in choices:
        return f"{correct_answer_label}. {choices[correct_answer_label]}"
    return correct_answer_label or ""


def extract_images(row: Tag, html_path: Path) -> list[ImageAsset]:
    images: list[ImageAsset] = []
    seen: set[Path] = set()
    for image in row.select("img[src]"):
        src = image.get("src")
        if not src:
            continue
        path = resolve_asset_path(src, html_path)
        if path in seen or not path.exists() or not path.is_file():
            continue
        seen.add(path)
        data = path.read_bytes()
        ext = path.suffix.lower().lstrip(".") or "jpg"
        images.append(
            ImageAsset(
                page_number=0,
                xref=None,
                bbox=(0.0, 0.0, 0.0, 0.0),
                ext=ext,
                data=data,
                width=0.0,
                height=0.0,
                area=0.0,
            )
        )
    return images


def resolve_asset_path(src: str, html_path: Path) -> Path:
    parsed = urlparse(src)
    raw_path = unquote(parsed.path or src)
    candidate = Path(raw_path)
    if candidate.is_absolute():
        return candidate
    return (html_path.parent / candidate).resolve()


def text_from_node(node: Tag | None) -> str:
    if node is None:
        return ""
    for hidden in node.select("script, style"):
        hidden.decompose()
    return normalize_inline_whitespace(node.get_text(" "))
