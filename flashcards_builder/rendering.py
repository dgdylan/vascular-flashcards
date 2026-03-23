from __future__ import annotations

import html
from collections import defaultdict
from pathlib import Path

from jinja2 import DictLoader, Environment, select_autoescape

from flashcards_builder.models import Flashcard
from flashcards_builder.utils import slugify


FLASHCARDS_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{ title }}</title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #06101d;
      --bg-strong: #0b1628;
      --card: rgba(17, 31, 52, 0.92);
      --card-strong: rgba(20, 36, 60, 0.98);
      --ink: #f4f8ff;
      --muted: #b0bfd6;
      --accent: #82ddd7;
      --accent-strong: #b4f0eb;
      --accent-soft: rgba(130, 221, 215, 0.16);
      --border: rgba(149, 180, 221, 0.34);
      --shadow: 0 26px 70px rgba(0, 0, 0, 0.42);
      --shadow-soft: 0 12px 28px rgba(0, 0, 0, 0.28);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Avenir Next", "Segoe UI", "Helvetica Neue", sans-serif;
      background:
        radial-gradient(circle at top left, rgba(130, 221, 215, 0.14), transparent 28%),
        radial-gradient(circle at 90% 10%, rgba(97, 130, 194, 0.18), transparent 24%),
        linear-gradient(180deg, #071221 0%, var(--bg) 54%, #040b15 100%);
      color: var(--ink);
      min-height: 100vh;
    }
    .wrap {
      width: min(1080px, calc(100% - 2rem));
      margin: 0 auto;
      padding: 1.5rem 0 4rem;
    }
    .hero {
      position: relative;
      overflow: hidden;
      margin-bottom: 1.5rem;
      padding: clamp(1.4rem, 2.5vw, 2rem);
      border: 1px solid var(--border);
      border-radius: 28px;
      background:
        linear-gradient(135deg, rgba(23, 40, 66, 0.98), rgba(14, 27, 47, 0.94)),
        linear-gradient(120deg, rgba(130, 221, 215, 0.08), rgba(97, 130, 194, 0.08));
      box-shadow: var(--shadow);
      backdrop-filter: blur(18px);
      animation: rise-in 560ms ease-out both;
    }
    .hero::after {
      content: "";
      position: absolute;
      inset: auto -8% -35% auto;
      width: 240px;
      aspect-ratio: 1;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(37, 99, 235, 0.18), transparent 70%);
      background: radial-gradient(circle, rgba(97, 130, 194, 0.4), transparent 70%);
      pointer-events: none;
    }
    .eyebrow {
      margin: 0 0 0.75rem;
      color: var(--accent);
      font-size: 0.78rem;
      font-weight: 800;
      letter-spacing: 0.18em;
      text-transform: uppercase;
    }
    h1 {
      margin: 0;
      font-size: clamp(2rem, 4.8vw, 3.8rem);
      line-height: 0.98;
      letter-spacing: -0.04em;
      max-width: 14ch;
      text-wrap: balance;
    }
    .subhead {
      margin: 1rem 0 0;
      color: var(--muted);
      font-size: clamp(0.98rem, 1.4vw, 1.08rem);
      line-height: 1.6;
      max-width: 60ch;
    }
    .toolbar {
      display: flex;
      flex-wrap: wrap;
      gap: 0.75rem;
      margin-bottom: 1.5rem;
    }
    .toolbar a, .toolbar button {
      border: 1px solid var(--border);
      background: var(--card-strong);
      color: var(--ink);
      border-radius: 999px;
      padding: 0.78rem 1.05rem;
      cursor: pointer;
      text-decoration: none;
      font: inherit;
      font-weight: 700;
      box-shadow: var(--shadow-soft);
      transition: transform 180ms ease, background-color 180ms ease, border-color 180ms ease;
    }
    .toolbar a:hover, .toolbar button:hover {
      transform: translateY(-1px);
      border-color: rgba(130, 221, 215, 0.42);
      background: rgba(26, 45, 73, 1);
    }
    .cards {
      display: grid;
      gap: 1rem;
    }
    .card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 24px;
      box-shadow: var(--shadow);
      overflow: hidden;
      backdrop-filter: blur(16px);
      animation: rise-in 520ms ease-out both;
      transition: transform 220ms ease, box-shadow 220ms ease, border-color 220ms ease;
    }
    .card:hover {
      transform: translateY(-3px);
      box-shadow: 0 30px 70px rgba(0, 0, 0, 0.38);
      border-color: rgba(130, 221, 215, 0.28);
    }
    .card-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
      padding: 1rem 1.2rem;
      border-bottom: 1px solid var(--border);
      background:
        linear-gradient(135deg, rgba(130, 221, 215, 0.09), rgba(97, 130, 194, 0.08)),
        rgba(16, 30, 50, 0.88);
    }
    .card-number {
      font-size: 0.9rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--accent);
      font-weight: 700;
    }
    .pill {
      padding: 0.3rem 0.65rem;
      border-radius: 999px;
      background: var(--accent-soft);
      color: var(--accent-strong);
      font-size: 0.85rem;
      font-weight: 700;
    }
    .card-body {
      padding: 1.2rem;
      display: grid;
      gap: 1rem;
    }
    .card-side {
      display: grid;
      gap: 0.75rem;
    }
    .label {
      font-size: 0.78rem;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      color: var(--muted);
      font-weight: 700;
    }
    .content {
      font-size: 1rem;
      line-height: 1.6;
      white-space: pre-wrap;
    }
    .choices {
      display: grid;
      gap: 0.45rem;
      padding: 0.9rem 1rem;
      border: 1px solid var(--border);
      border-radius: 14px;
      background: linear-gradient(180deg, rgba(24, 41, 67, 0.98), rgba(17, 31, 52, 0.92));
    }
    .choice {
      line-height: 1.5;
    }
    .choice-label {
      font-weight: 700;
      color: var(--accent);
      margin-right: 0.3rem;
    }
    img {
      max-width: 100%;
      height: auto;
      border-radius: 18px;
      border: 1px solid var(--border);
      background: rgba(8, 15, 27, 0.96);
      display: block;
      box-shadow: var(--shadow-soft);
    }
    details {
      border-top: 1px dashed rgba(149, 180, 221, 0.34);
      padding-top: 1rem;
    }
    summary {
      cursor: pointer;
      color: var(--accent);
      font-weight: 700;
      list-style: none;
      transition: color 180ms ease;
    }
    summary:hover { color: var(--accent-strong); }
    summary::-webkit-details-marker { display: none; }
    .answer-block {
      margin-top: 0.9rem;
      display: grid;
      gap: 0.75rem;
      padding: 1rem;
      border: 1px solid var(--border);
      border-radius: 16px;
      background: linear-gradient(180deg, rgba(19, 35, 58, 0.98), rgba(13, 25, 43, 0.96));
    }
    .answer-title {
      font-weight: 700;
    }
    @keyframes rise-in {
      from {
        opacity: 0;
        transform: translateY(16px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }
    @media (prefers-reduced-motion: reduce) {
      .hero, .card {
        animation: none;
      }
      .toolbar a, .toolbar button, .card, summary {
        transition: none;
      }
    }
    @media (max-width: 640px) {
      .wrap { width: min(100% - 1rem, 1080px); padding-top: 1rem; }
      .hero {
        border-radius: 22px;
        padding: 1.15rem;
      }
      .card-header, .card-body { padding: 1rem; }
      .toolbar {
        display: grid;
        grid-template-columns: 1fr;
      }
      .toolbar a, .toolbar button {
        width: 100%;
        text-align: center;
      }
      h1 {
        max-width: none;
      }
    }
  </style>
</head>
<body>
  <main class="wrap">
    <section class="hero">
      <p class="eyebrow">Review Deck</p>
      <h1>{{ title }}</h1>
      <p class="subhead">{{ flashcards|length }} flashcards extracted from this PDF. Open each back panel to review the correct answer and full feedback.</p>
      <div class="toolbar">
        <a href="../index.html">Back to index</a>
        <button type="button" id="open-all">Open all backs</button>
        <button type="button" id="close-all">Close all backs</button>
      </div>
    </section>
    <section class="cards">
      {% for flashcard in flashcards %}
      <article class="card" id="q{{ flashcard.number }}" style="animation-delay: {{ loop.index0 * 35 }}ms;">
        <div class="card-header">
          <div class="card-number">Question {{ flashcard.number }}</div>
          {% if flashcard.is_missed %}<div class="pill">Missed</div>{% endif %}
        </div>
        <div class="card-body">
          <section class="card-side">
            <div class="label">Front</div>
            <div class="content">{{ flashcard.question }}</div>
            {% if flashcard.choices %}
            <div class="choices">
              {% for label, text in flashcard.choices.items() %}
              <div class="choice"><span class="choice-label">{{ label }}:</span>{{ text }}</div>
              {% endfor %}
            </div>
            {% endif %}
            {% for image_name in image_names(flashcard) %}
            <img src="media/{{ image_name }}" alt="Question {{ flashcard.number }} image">
            {% endfor %}
          </section>
          <details>
            <summary>Show answer and feedback</summary>
            <div class="answer-block">
              <div><span class="answer-title">Answer:</span> {{ flashcard.answer or "Unavailable" }}</div>
              <div class="content"><span class="answer-title">Feedback:</span><br>{{ flashcard.feedback }}</div>
            </div>
          </details>
        </div>
      </article>
      {% endfor %}
    </section>
  </main>
  <script>
    const detailsElements = Array.from(document.querySelectorAll("details"));
    document.getElementById("open-all").addEventListener("click", () => detailsElements.forEach((item) => item.open = true));
    document.getElementById("close-all").addEventListener("click", () => detailsElements.forEach((item) => item.open = false));
  </script>
</body>
</html>
""".strip()


INDEX_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Flashcard Index</title>
  <style>
    :root {
      --bg: #06101d;
      --ink: #f4f8ff;
      --muted: #b0bfd6;
      --accent: #82ddd7;
      --border: rgba(149, 180, 221, 0.34);
      --shadow: 0 26px 70px rgba(0, 0, 0, 0.42);
      --shadow-soft: 0 12px 28px rgba(0, 0, 0, 0.28);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Avenir Next", "Segoe UI", "Helvetica Neue", sans-serif;
      background:
        radial-gradient(circle at top left, rgba(130, 221, 215, 0.14), transparent 28%),
        radial-gradient(circle at 90% 10%, rgba(97, 130, 194, 0.18), transparent 24%),
        linear-gradient(180deg, #071221 0%, var(--bg) 54%, #040b15 100%);
      color: var(--ink);
    }
    .wrap {
      width: min(1080px, calc(100% - 2rem));
      margin: 0 auto;
      padding: 1.5rem 0 4rem;
    }
    .hero {
      margin-bottom: 1.75rem;
      padding: clamp(1.4rem, 2.5vw, 2rem);
      border: 1px solid var(--border);
      border-radius: 28px;
      background:
        linear-gradient(135deg, rgba(23, 40, 66, 0.98), rgba(14, 27, 47, 0.94)),
        linear-gradient(120deg, rgba(130, 221, 215, 0.08), rgba(97, 130, 194, 0.08));
      box-shadow: var(--shadow);
      backdrop-filter: blur(18px);
      animation: rise-in 560ms ease-out both;
    }
    .eyebrow {
      margin: 0 0 0.75rem;
      color: var(--accent);
      font-size: 0.78rem;
      font-weight: 800;
      letter-spacing: 0.18em;
      text-transform: uppercase;
    }
    h1 {
      margin: 0;
      font-size: clamp(2rem, 4.8vw, 3.8rem);
      line-height: 0.98;
      letter-spacing: -0.04em;
      max-width: 12ch;
      text-wrap: balance;
    }
    p {
      color: var(--muted);
      max-width: 48rem;
      line-height: 1.65;
    }
    .group {
      margin-top: 2rem;
      padding-inline: 0.5rem;
    }
    .group h2 {
      margin-bottom: 0.7rem;
      font-size: 1.3rem;
      letter-spacing: -0.02em;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 1rem;
    }
    .item {
      background: rgba(12, 24, 42, 0.82);
      border: 1px solid var(--border);
      border-radius: 22px;
      padding: 1.1rem;
      box-shadow: var(--shadow-soft);
      backdrop-filter: blur(14px);
      animation: rise-in 520ms ease-out both;
      transition: transform 220ms ease, box-shadow 220ms ease, border-color 220ms ease;
    }
    .item:hover {
      transform: translateY(-3px);
      box-shadow: var(--shadow);
      border-color: rgba(130, 221, 215, 0.28);
    }
    .item a {
      color: var(--accent);
      text-decoration: none;
      font-weight: 700;
      font-size: 1.05rem;
    }
    .meta {
      margin-top: 0.45rem;
      color: var(--muted);
      font-size: 0.95rem;
    }
    @keyframes rise-in {
      from {
        opacity: 0;
        transform: translateY(16px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }
    @media (prefers-reduced-motion: reduce) {
      .hero, .item {
        animation: none;
      }
      .item {
        transition: none;
      }
    }
    @media (max-width: 640px) {
      .wrap {
        width: min(100% - 1rem, 1080px);
        padding-top: 1rem;
      }
      .hero {
        border-radius: 22px;
        padding: 1.15rem;
      }
      h1 {
        max-width: none;
      }
      .grid {
        grid-template-columns: 1fr;
      }
      .group {
        padding-inline: 0.2rem;
      }
    }
  </style>
</head>
<body>
  <main class="wrap">
    <section class="hero">
      <p class="eyebrow">Flashcard Library</p>
      <h1>Flashcard Index</h1>
      <p>Each entry links to a per-PDF flashcard page and companion TSV export. The layout is designed for quick browsing on desktop and mobile.</p>
    </section>
    {% for group_name, items in groups %}
    <section class="group">
      <h2>{{ group_name }}</h2>
      <div class="grid">
        {% for entry in items %}
        <article class="item" style="animation-delay: {{ loop.index0 * 35 }}ms;">
          <a href="{{ entry.href }}">{{ entry.title }}</a>
          <div class="meta">{{ entry.count }} cards</div>
          <div class="meta"><a href="{{ entry.tsv_href }}">TSV export</a>{% if entry.json_href %} · <a href="{{ entry.json_href }}">JSON export</a>{% endif %}</div>
        </article>
        {% endfor %}
      </div>
    </section>
    {% endfor %}
  </main>
</body>
</html>
""".strip()


ENVIRONMENT = Environment(
    loader=DictLoader(
        {
            "flashcards.html": FLASHCARDS_TEMPLATE,
            "index.html": INDEX_TEMPLATE,
        }
    ),
    autoescape=select_autoescape(("html", "xml")),
)
ENVIRONMENT.filters["image_names"] = lambda flashcard: [image.saved_name for image in flashcard.images if image.saved_name]


def render_flashcards_page(*, title: str, flashcards: list[Flashcard]) -> str:
    template = ENVIRONMENT.get_template("flashcards.html")
    return template.render(title=title, flashcards=flashcards, image_names=image_names)


def render_index_page(*, entries: list[dict], group_by_title: bool) -> str:
    groups: dict[str, list[dict]] = defaultdict(list)
    for entry in entries:
        group_name = grouped_title(entry["title"]) if group_by_title else "All PDFs"
        groups[group_name].append(
            {
                "title": entry["title"],
                "count": entry["count"],
                "href": relative_href(entry["path"]),
                "tsv_href": relative_href(entry["tsv_path"]),
                "json_href": relative_href(entry["json_path"]) if entry["json_path"] else None,
            }
        )

    ordered_groups = sorted(groups.items(), key=lambda item: item[0].lower())
    template = ENVIRONMENT.get_template("index.html")
    return template.render(groups=ordered_groups)


def relative_href(path: Path | None) -> str | None:
    if path is None:
        return None
    return html.escape(path.as_posix())


def grouped_title(title: str) -> str:
    slug = slugify(title)
    prefix = slug.split("-")[0] if "-" in slug else slug
    return prefix.replace("-", " ").title() or "Other"


def image_names(flashcard: Flashcard) -> list[str]:
    return [image.saved_name for image in flashcard.images if image.saved_name]
