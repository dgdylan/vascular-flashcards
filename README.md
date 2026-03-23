# PDF Exam Review Flashcard Builder

Convert a folder of machine-readable exam-review PDFs into per-PDF flashcard pages, Anki-importable TSV files, and extracted media folders.

## Features

- Recursively scans an input folder for `.pdf` files
- Builds one output folder per PDF using a sanitized slug
- Extracts question text, correct answer, and full feedback
- Associates large nearby embedded images with the relevant question
- Writes:
  - `flashcards.html`
  - `flashcards.tsv`
  - `media/`
  - optional `flashcards.json`
- Generates an `output/index.html` linking to every generated page
- Supports `--missed-only`, `--include-choices`, `--debug`, `--combine-index-sections`, and `--export-json`

## Requirements

- Python 3.9+
- [PyMuPDF](https://pymupdf.readthedocs.io/)
- [Jinja2](https://jinja.palletsprojects.com/)

Install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

Run against a folder of PDFs:

```bash
python3 build_flashcards.py --input ./pdfs --output ./output
```

Useful options:

```bash
python3 build_flashcards.py \
  --input ./pdfs \
  --output ./output \
  --missed-only \
  --include-choices \
  --export-json \
  --debug
```

## Output Layout

```text
output/
  index.html
  module-1/
    flashcards.html
    flashcards.tsv
    flashcards.json
    media/
      q1.png
      q5.jpg
  module-2/
    flashcards.html
    flashcards.tsv
    media/
      q2.png
```

## Parsing Rules

- Question fronts include:
  - question text
  - question image(s), when a large nearby image is detected
- Card backs include:
  - correct answer only
  - full feedback text
- If `Correct answer is:` is missing, the script assumes `You answered:` is correct
- Small logos, header/footer images, and decorative assets are filtered out
- Questions may span pages; the parser keeps collecting blocks until the next numbered question begins

## Anki Notes

- `flashcards.tsv` contains two columns:
  - Front HTML
  - Back HTML
- Front HTML uses `<img src="filename.ext">` tags. For Anki to show those images:
  1. Import the TSV into Anki.
  2. Copy the corresponding files from each generated `media/` folder into Anki's `collection.media` folder.
- If you keep per-deck media organized elsewhere first, make sure the final filenames copied into `collection.media` match the filenames referenced in the TSV.

## Development Notes

- Main CLI entrypoint: [build_flashcards.py](/Users/dylan/Documents/Study - VASC/build_flashcards.py)
- Package entrypoint: [flashcards_builder/cli.py](/Users/dylan/Documents/Study - VASC/flashcards_builder/cli.py)
- The parser uses PyMuPDF block coordinates to reduce header/footer noise and to assign each extracted image to a single nearest question when possible.
