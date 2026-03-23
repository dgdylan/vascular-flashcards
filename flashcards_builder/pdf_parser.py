from __future__ import annotations

import logging
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import fitz

from flashcards_builder.models import Flashcard, ImageAsset, QuestionBlock, TextBlock
from flashcards_builder.utils import clean_text, normalize_inline_whitespace


LOGGER = logging.getLogger(__name__)

QUESTION_START_RE = re.compile(r"^\s*(\d+)\.(?:\s+|$)(.*)$")
CHOICE_RE = re.compile(r"^\s*([A-Z]):\s*(.*)$")
YOU_ANSWERED_RE = re.compile(r"You answered:\s*([A-Z])", re.IGNORECASE)
CORRECT_ANSWER_RE = re.compile(r"Correct answer is:\s*([A-Z])", re.IGNORECASE)
POINTS_RE = re.compile(r"Points:\s*([0-9.]+)\s*/\s*([0-9.]+)", re.IGNORECASE)
HEADER_NOISE_RE = re.compile(
    r"(ardms vasc ctl|exam summary|exam review|support|profile|log out|welcome back|completed:|status:|passing score:|correct answers in blue|incorrect answers in red|\bexams\b|\btraining\b|\bresults\b|\bfb\b|^[A-Za-z]+!$)",
    re.IGNORECASE,
)


@dataclass
class ParseOptions:
    include_choices: bool = False
    missed_only: bool = False
    debug: bool = False


@dataclass
class ParsedPdf:
    source_pdf: Path
    title: str
    slug: str
    flashcards: list[Flashcard]
    warnings: list[str]


def parse_pdf(pdf_path: Path, *, options: ParseOptions) -> tuple[list[Flashcard], list[str]]:
    warnings: list[str] = []
    flashcards: list[Flashcard] = []

    try:
        with fitz.open(pdf_path) as document:
            text_blocks_by_page, images_by_page = extract_page_content(document)
            question_blocks = detect_question_blocks(pdf_path, text_blocks_by_page)
            assign_images(question_blocks, images_by_page, debug=options.debug)

            for block in question_blocks:
                flashcard = parse_question_block(block, include_choices=options.include_choices)
                if flashcard is None:
                    continue
                if options.missed_only and not flashcard.is_missed:
                    continue
                flashcards.append(flashcard)
    except Exception as exc:  # pragma: no cover - defensive parsing for malformed PDFs
        warnings.append(f"Failed to parse {pdf_path.name}: {exc}")
        LOGGER.exception("Failed to parse %s", pdf_path)

    return flashcards, warnings


def extract_page_content(
    document: fitz.Document,
) -> tuple[dict[int, list[TextBlock]], dict[int, list[ImageAsset]]]:
    text_blocks_by_page: dict[int, list[TextBlock]] = {}
    images_by_page: dict[int, list[ImageAsset]] = {}

    for page_index, page in enumerate(document, start=1):
        page_rect = page.rect
        raw_blocks = page.get_text("dict").get("blocks", [])
        text_blocks: list[TextBlock] = []
        image_blocks: list[ImageAsset] = []

        for raw_block in raw_blocks:
            block_type = raw_block.get("type")
            bbox_tuple = tuple(raw_block.get("bbox", (0, 0, 0, 0)))
            bbox = fitz.Rect(bbox_tuple)

            if block_type == 0:
                lines = []
                for line in raw_block.get("lines", []):
                    spans = [span.get("text", "") for span in line.get("spans", [])]
                    line_text = clean_text("".join(spans))
                    if line_text:
                        lines.append(line_text)

                if not lines:
                    continue

                text = "\n".join(lines).strip()
                if should_skip_text_block(text=text, bbox=bbox, page_rect=page_rect):
                    continue
                text_blocks.append(
                    TextBlock(
                        page_number=page_index,
                        bbox=bbox_tuple,
                        text=text,
                        raw_lines=lines,
                    )
                )
            elif block_type == 1:
                image = build_image_asset(page_index, raw_block)
                if image and not should_skip_image(image=image, page_rect=page_rect):
                    image_blocks.append(image)

        text_blocks_by_page[page_index] = sorted(text_blocks, key=_sort_key)
        images_by_page[page_index] = sorted(image_blocks, key=lambda image: (image.bbox[1], image.bbox[0]))

    return text_blocks_by_page, images_by_page


def should_skip_text_block(*, text: str, bbox: fitz.Rect, page_rect: fitz.Rect) -> bool:
    normalized = normalize_inline_whitespace(text)
    if not normalized:
        return True
    if bbox.y0 < page_rect.height * 0.08 and HEADER_NOISE_RE.search(normalized):
        return True
    return False


def build_image_asset(page_number: int, raw_block: dict) -> ImageAsset | None:
    image_bytes = raw_block.get("image")
    if not image_bytes:
        return None

    bbox_tuple = tuple(raw_block.get("bbox", (0, 0, 0, 0)))
    width = max(0.0, bbox_tuple[2] - bbox_tuple[0])
    height = max(0.0, bbox_tuple[3] - bbox_tuple[1])
    return ImageAsset(
        page_number=page_number,
        xref=raw_block.get("xref"),
        bbox=bbox_tuple,
        ext=(raw_block.get("ext") or "png").lower(),
        data=image_bytes,
        width=width,
        height=height,
        area=width * height,
    )


def should_skip_image(*, image: ImageAsset, page_rect: fitz.Rect) -> bool:
    if image.area < 15000:
        return True
    if image.width < 100 or image.height < 100:
        return True
    if image.bbox[1] < page_rect.height * 0.12 and image.area < 120000:
        return True
    if image.bbox[3] > page_rect.height * 0.97 and image.area < 120000:
        return True
    return False


def detect_question_blocks(
    pdf_path: Path,
    text_blocks_by_page: dict[int, list[TextBlock]],
) -> list[QuestionBlock]:
    ordered_blocks = [
        block
        for page_number in sorted(text_blocks_by_page)
        for block in text_blocks_by_page[page_number]
    ]

    question_blocks: list[QuestionBlock] = []
    current: list[TextBlock] = []
    current_number: int | None = None

    for block in ordered_blocks:
        number = extract_question_number(block)
        if number is not None:
            if current and current_number is not None:
                question_blocks.append(build_question_block(pdf_path, current_number, current))
            current = [block]
            current_number = number
            continue

        if current:
            current.append(block)

    if current and current_number is not None:
        question_blocks.append(build_question_block(pdf_path, current_number, current))

    return question_blocks


def extract_question_number(block: TextBlock) -> int | None:
    first_line = block.raw_lines[0] if block.raw_lines else ""
    match = QUESTION_START_RE.match(first_line)
    if match:
        return int(match.group(1))
    return None


def build_question_block(pdf_path: Path, number: int, blocks: list[TextBlock]) -> QuestionBlock:
    points_earned, points_possible = extract_points(blocks)
    raw_text = "\n".join(block.text for block in blocks).strip()
    bbox = merge_bboxes([block.bbox for block in blocks])
    page_numbers = sorted({block.page_number for block in blocks})
    return QuestionBlock(
        number=number,
        source_pdf=pdf_path,
        raw_text=raw_text,
        text_blocks=blocks,
        page_numbers=page_numbers,
        start_page=page_numbers[0],
        end_page=page_numbers[-1],
        bbox=bbox,
        points_earned=points_earned,
        points_possible=points_possible,
    )


def extract_points(blocks: list[TextBlock]) -> tuple[float | None, float | None]:
    for block in blocks:
        match = POINTS_RE.search(block.text)
        if match:
            return float(match.group(1)), float(match.group(2))
    return None, None


def merge_bboxes(bboxes: list[tuple[float, float, float, float]]) -> tuple[float, float, float, float]:
    x0 = min(bbox[0] for bbox in bboxes)
    y0 = min(bbox[1] for bbox in bboxes)
    x1 = max(bbox[2] for bbox in bboxes)
    y1 = max(bbox[3] for bbox in bboxes)
    return (x0, y0, x1, y1)


def assign_images(
    question_blocks: list[QuestionBlock],
    images_by_page: dict[int, list[ImageAsset]],
    *,
    debug: bool,
) -> None:
    used_images: set[tuple[int, tuple[float, float, float, float]]] = set()
    questions_by_page: dict[int, list[QuestionBlock]] = defaultdict(list)
    for block in question_blocks:
        for page_number in block.page_numbers:
            questions_by_page[page_number].append(block)

    for page_number, images in images_by_page.items():
        page_questions = questions_by_page.get(page_number, [])
        if not page_questions:
            continue

        for image in images:
            image_key = (page_number, image.bbox)
            if image_key in used_images:
                continue
            owner = choose_image_owner(image, page_questions)
            if owner is None:
                continue
            owner.images.append(image)
            used_images.add(image_key)
            if debug:
                LOGGER.debug(
                    "Assigned image page=%s bbox=%s to question=%s",
                    page_number,
                    image.bbox,
                    owner.number,
                )


def choose_image_owner(image: ImageAsset, page_questions: list[QuestionBlock]) -> QuestionBlock | None:
    best_question: QuestionBlock | None = None
    best_score: tuple[float, float] | None = None
    image_center_y = (image.bbox[1] + image.bbox[3]) / 2

    for question in page_questions:
        q_blocks = [block for block in question.text_blocks if block.page_number == image.page_number]
        if not q_blocks:
            continue

        page_bboxes = [block.bbox for block in q_blocks]
        top = min(bbox[1] for bbox in page_bboxes)
        bottom = max(bbox[3] for bbox in page_bboxes)

        if image.bbox[3] < top - 80:
            continue

        vertical_gap = 0.0
        if image_center_y < top:
            vertical_gap = top - image_center_y
        elif image_center_y > bottom:
            vertical_gap = image_center_y - bottom

        overlap_bonus = 0.0
        if image.bbox[1] <= bottom and image.bbox[3] >= top:
            overlap_bonus = -200.0

        score = (vertical_gap + overlap_bonus, abs(image.bbox[0] - min(bbox[0] for bbox in page_bboxes)))
        if best_score is None or score < best_score:
            best_score = score
            best_question = question

    return best_question


def parse_question_block(block: QuestionBlock, *, include_choices: bool) -> Flashcard | None:
    question_lines: list[str] = []
    choices: dict[str, str] = {}
    feedback_lines: list[str] = []
    user_answer: str | None = None
    correct_answer_label: str | None = None

    state = "question"
    current_choice: str | None = None

    for text_block in block.text_blocks:
        for raw_line in text_block.raw_lines:
            line = clean_text(raw_line)
            if not line:
                continue

            line = strip_question_number(block.number, line)
            line = strip_points(line)
            if not line:
                continue

            if line.startswith("Feedback:"):
                state = "feedback"
                current_choice = None
                tail = line.partition("Feedback:")[2].strip()
                if tail:
                    feedback_lines.append(tail)
                continue

            if state == "feedback":
                feedback_lines.append(line)
                continue

            user_match = YOU_ANSWERED_RE.search(line)
            if user_match:
                user_answer = user_match.group(1).upper()
                line = YOU_ANSWERED_RE.sub("", line).strip()

            correct_match = CORRECT_ANSWER_RE.search(line)
            if correct_match:
                correct_answer_label = correct_match.group(1).upper()
                line = CORRECT_ANSWER_RE.sub("", line).strip()

            choice_match = CHOICE_RE.match(line)
            if choice_match:
                state = "choices"
                current_choice = choice_match.group(1).upper()
                choices[current_choice] = choice_match.group(2).strip()
                continue

            if state == "choices" and current_choice:
                if line:
                    choices[current_choice] = f"{choices[current_choice]} {line}".strip()
                continue

            if line:
                question_lines.append(line)

    question = normalize_inline_whitespace(" ".join(question_lines))
    feedback = "\n".join(line.strip() for line in feedback_lines if line.strip()).strip()
    feedback = normalize_feedback(feedback)

    if not question:
        return None

    if not correct_answer_label and user_answer:
        correct_answer_label = user_answer

    answer = resolve_answer_text(correct_answer_label, choices, user_answer, include_choices=include_choices)
    return Flashcard(
        number=block.number,
        question=question,
        answer=answer,
        feedback=feedback,
        source_pdf=block.source_pdf,
        choices=choices,
        user_answer=user_answer,
        correct_answer_label=correct_answer_label,
        images=list(block.images),
        page_numbers=block.page_numbers,
        points_earned=block.points_earned,
        points_possible=block.points_possible,
        raw_text=block.raw_text,
    )


def strip_question_number(question_number: int, line: str) -> str:
    match = QUESTION_START_RE.match(line)
    if match and int(match.group(1)) == question_number:
        return match.group(2).strip()
    return line


def strip_points(line: str) -> str:
    line = POINTS_RE.sub("", line)
    return normalize_inline_whitespace(line)


def normalize_feedback(feedback: str) -> str:
    normalized_lines = [normalize_inline_whitespace(line) for line in feedback.splitlines() if line.strip()]
    return "\n".join(normalized_lines).strip()


def resolve_answer_text(
    correct_answer_label: str | None,
    choices: dict[str, str],
    user_answer: str | None,
    *,
    include_choices: bool,
) -> str:
    if correct_answer_label and correct_answer_label in choices:
        return f"{correct_answer_label}. {choices[correct_answer_label]}"

    if correct_answer_label:
        return correct_answer_label

    if user_answer and user_answer in choices:
        if include_choices:
            return f"{user_answer}. {choices[user_answer]}"
        return f"{user_answer}. {choices[user_answer]}"

    if include_choices and choices:
        return " | ".join(f"{label}. {text}" for label, text in choices.items())

    return ""


def _sort_key(block: TextBlock) -> tuple[float, float]:
    return (block.bbox[1], block.bbox[0])
