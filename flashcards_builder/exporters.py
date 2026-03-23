from __future__ import annotations

import csv
import html
import json
import logging
from pathlib import Path

from flashcards_builder.models import Flashcard
from flashcards_builder.rendering import render_flashcards_page, render_index_page
from flashcards_builder.utils import ensure_directory


LOGGER = logging.getLogger(__name__)


def save_flashcard_assets(flashcards: list[Flashcard], media_dir: Path, *, debug: bool) -> None:
    ensure_directory(media_dir)
    seen_names: set[str] = set()

    for flashcard in flashcards:
        for image_index, image in enumerate(flashcard.images, start=1):
            ext = "jpg" if image.ext == "jpeg" else image.ext
            filename = f"q{flashcard.number}"
            if len(flashcard.images) > 1:
                filename = f"{filename}_{image_index}"
            filename = f"{filename}.{ext}"
            counter = 2
            while filename in seen_names:
                filename = f"q{flashcard.number}_{image_index}_{counter}.{ext}"
                counter += 1
            (media_dir / filename).write_bytes(image.data)
            image.saved_name = filename
            seen_names.add(filename)
            if debug:
                LOGGER.debug("Saved image for question %s -> %s", flashcard.number, filename)


def write_tsv(flashcards: list[Flashcard], destination: Path) -> None:
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        for flashcard in flashcards:
            writer.writerow([build_front_html(flashcard), build_back_html(flashcard)])


def write_json(flashcards: list[Flashcard], destination: Path) -> None:
    payload = [flashcard.to_dict() for flashcard in flashcards]
    destination.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_flashcards_html(title: str, flashcards: list[Flashcard], destination: Path) -> None:
    destination.write_text(render_flashcards_page(title=title, flashcards=flashcards), encoding="utf-8")


def write_index_html(entries: list[dict], destination: Path, *, group_by_title: bool) -> None:
    destination.write_text(
        render_index_page(entries=entries, group_by_title=group_by_title),
        encoding="utf-8",
    )


def build_front_html(flashcard: Flashcard) -> str:
    parts = [html.escape(flashcard.question)]
    if flashcard.choices:
        parts.append(format_choices_html(flashcard))
    for image_name in image_names(flashcard):
        parts.append(f'<img src="{html.escape(image_name)}" alt="Question {flashcard.number} image">')
    return "<br><br>".join(parts)


def build_back_html(flashcard: Flashcard) -> str:
    answer = html.escape(flashcard.answer) if flashcard.answer else "Unavailable"
    feedback = html.escape(flashcard.feedback).replace("\n", "<br>")
    return f"<b>Answer:</b> {answer}<br><br><b>Feedback:</b><br>{feedback}"


def image_names(flashcard: Flashcard) -> list[str]:
    return [image.saved_name for image in flashcard.images if image.saved_name]


def format_choices_html(flashcard: Flashcard) -> str:
    rendered = []
    for label, text in flashcard.choices.items():
        rendered.append(f"<b>{html.escape(label)}:</b> {html.escape(text)}")
    return "<br>".join(rendered)


def prepare_output_bundle(
    *,
    title: str,
    flashcards: list[Flashcard],
    destination_dir: Path,
    export_json: bool,
    debug: bool,
) -> dict:
    ensure_directory(destination_dir)
    media_dir = ensure_directory(destination_dir / "media")
    save_flashcard_assets(flashcards, media_dir, debug=debug)

    html_path = destination_dir / "flashcards.html"
    tsv_path = destination_dir / "flashcards.tsv"
    json_path = destination_dir / "flashcards.json"

    write_flashcards_html(title, flashcards, html_path)
    write_tsv(flashcards, tsv_path)
    if export_json:
        write_json(flashcards, json_path)

    return {
        "title": title,
        "path": html_path,
        "tsv_path": tsv_path,
        "json_path": json_path if export_json else None,
        "count": len(flashcards),
        "destination_dir": destination_dir,
    }
