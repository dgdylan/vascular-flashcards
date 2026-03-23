from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from flashcards_builder.exporters import prepare_output_bundle, write_index_html
from flashcards_builder.pdf_parser import ParseOptions, parse_pdf
from flashcards_builder.utils import ensure_directory, humanize_pdf_title, slugify


LOGGER = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert exam-review PDFs into per-PDF flashcard HTML and Anki TSV exports."
    )
    parser.add_argument("--input", type=Path, required=True, help="Input folder to scan recursively for PDFs.")
    parser.add_argument("--output", type=Path, required=True, help="Output folder for generated flashcards.")
    parser.add_argument(
        "--missed-only",
        action="store_true",
        help="Only export questions that were answered incorrectly.",
    )
    parser.add_argument(
        "--include-choices",
        action="store_true",
        help="Keep full answer choices in the structured data and use them as answer fallback.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print parsing diagnostics and warnings.",
    )
    parser.add_argument(
        "--combine-index-sections",
        action="store_true",
        help="Group index sections by the leading word of the PDF title.",
    )
    parser.add_argument(
        "--export-json",
        action="store_true",
        help="Also write structured question data as flashcards.json for each PDF.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    configure_logging(args.debug)

    input_dir = args.input.expanduser().resolve()
    output_dir = ensure_directory(args.output.expanduser().resolve())

    if not input_dir.exists() or not input_dir.is_dir():
        parser.error(f"Input directory does not exist: {input_dir}")

    pdf_files = sorted(path for path in input_dir.rglob("*.pdf") if path.is_file())
    if not pdf_files:
        LOGGER.error("No PDFs found under %s", input_dir)
        return 1

    options = ParseOptions(
        include_choices=args.include_choices,
        missed_only=args.missed_only,
        debug=args.debug,
    )

    index_entries: list[dict] = []
    had_warnings = False

    for pdf_path in pdf_files:
        title = humanize_pdf_title(pdf_path.stem)
        slug = slugify(pdf_path.stem)
        destination_dir = ensure_directory(output_dir / slug)
        flashcards, warnings = parse_pdf(pdf_path, options=options)

        for warning in warnings:
            had_warnings = True
            LOGGER.warning(warning)

        bundle = prepare_output_bundle(
            title=title,
            flashcards=flashcards,
            destination_dir=destination_dir,
            export_json=args.export_json,
            debug=args.debug,
        )
        bundle["path"] = bundle["path"].relative_to(output_dir)
        bundle["tsv_path"] = bundle["tsv_path"].relative_to(output_dir)
        if bundle["json_path"] is not None:
            bundle["json_path"] = bundle["json_path"].relative_to(output_dir)
        index_entries.append(bundle)
        LOGGER.info("Processed %s -> %s cards", pdf_path.name, len(flashcards))

    write_index_html(
        index_entries,
        output_dir / "index.html",
        group_by_title=args.combine_index_sections,
    )
    LOGGER.info("Wrote index -> %s", output_dir / "index.html")
    return 0 if not had_warnings else 0


def configure_logging(debug: bool) -> None:
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s", stream=sys.stdout)
