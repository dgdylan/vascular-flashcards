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
      --bg: #32435c;
      --bg-strong: #29384d;
      --card: rgba(44, 58, 81, 0.94);
      --card-strong: rgba(48, 63, 88, 0.98);
      --ink: #fff7e8;
      --muted: #d8d9e6;
      --accent: #45e3ff;
      --accent-strong: #6f88fc;
      --heading: #fffaf0;
      --subheading: #f5efe0;
      --success: #45e3ff;
      --danger: #a163f7;
      --warning: #fff582;
      --accent-soft: rgba(69, 227, 255, 0.16);
      --border: rgba(255, 245, 130, 0.2);
      --shadow: 0 26px 70px rgba(0, 0, 0, 0.42);
      --shadow-soft: 0 12px 28px rgba(0, 0, 0, 0.28);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Avenir Next", "Segoe UI", "Helvetica Neue", sans-serif;
      background:
        radial-gradient(circle at top left, rgba(161, 99, 247, 0.16), transparent 28%),
        radial-gradient(circle at 90% 10%, rgba(69, 227, 255, 0.12), transparent 24%),
        linear-gradient(180deg, #31415a 0%, var(--bg) 54%, #29384d 100%);
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
        linear-gradient(135deg, rgba(61, 78, 108, 0.98), rgba(44, 58, 81, 0.94)),
        linear-gradient(120deg, rgba(161, 99, 247, 0.1), rgba(69, 227, 255, 0.08));
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
      background: radial-gradient(circle, rgba(111, 136, 252, 0.34), transparent 70%);
      pointer-events: none;
    }
    .eyebrow {
      margin: 0 0 0.75rem;
      color: var(--warning);
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
      color: var(--heading);
    }
    .subhead {
      margin: 1rem 0 0;
      color: var(--subheading);
      font-size: clamp(0.98rem, 1.4vw, 1.08rem);
      line-height: 1.6;
      max-width: 60ch;
    }
    .hero-stats {
      display: flex;
      flex-wrap: wrap;
      gap: 0.8rem;
      margin-top: 1rem;
    }
    .hero-stat {
      padding: 0.72rem 0.95rem;
      border-radius: 16px;
      background: rgba(39, 52, 73, 0.52);
      border: 1px solid var(--border);
      color: var(--ink);
      min-width: 120px;
    }
    .hero-stat strong {
      display: block;
      font-size: 1rem;
      color: var(--heading);
    }
    .hero-stat span {
      display: block;
      margin-top: 0.18rem;
      font-size: 0.82rem;
      color: var(--muted);
      letter-spacing: 0.06em;
      text-transform: uppercase;
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
      border-color: rgba(69, 227, 255, 0.38);
      background: rgba(62, 81, 113, 1);
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
      border-color: rgba(69, 227, 255, 0.26);
    }
    .card-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
      padding: 1rem 1.2rem;
      border-bottom: 1px solid var(--border);
      background:
        linear-gradient(135deg, rgba(161, 99, 247, 0.12), rgba(69, 227, 255, 0.08)),
        rgba(51, 67, 92, 0.88);
    }
    .card-number {
      font-size: 0.9rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--warning);
      font-weight: 700;
    }
    .pill {
      padding: 0.3rem 0.65rem;
      border-radius: 999px;
      background: rgba(161, 99, 247, 0.16);
      color: #f3ddff;
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
      color: #d9dcf5;
      font-weight: 700;
    }
    .content {
      font-size: 1rem;
      line-height: 1.7;
      white-space: pre-wrap;
    }
    .question-text {
      font-size: clamp(1.02rem, 1.45vw, 1.16rem);
      color: var(--heading);
      font-weight: 650;
      letter-spacing: -0.01em;
    }
    .choices {
      display: grid;
      gap: 0.65rem;
      padding: 0.95rem 1rem;
      border: 1px solid var(--border);
      border-radius: 14px;
      background: linear-gradient(180deg, rgba(53, 70, 98, 0.98), rgba(43, 57, 79, 0.92));
    }
    .choice {
      appearance: none;
      width: 100%;
      text-align: left;
      font: inherit;
      color: var(--ink);
      line-height: 1.55;
      padding: 0.75rem 0.9rem;
      border-radius: 12px;
      border: 1px solid rgba(255, 245, 130, 0.08);
      background: rgba(39, 52, 73, 0.6);
      cursor: pointer;
      transition: transform 160ms ease, border-color 160ms ease, background-color 160ms ease;
    }
    .choice:hover {
      transform: translateY(-1px);
      border-color: rgba(69, 227, 255, 0.34);
      background: rgba(57, 75, 104, 0.82);
    }
    .choice-label {
      font-weight: 700;
      color: var(--warning);
      margin-right: 0.3rem;
    }
    .choice.correct {
      border-color: rgba(69, 227, 255, 0.55);
      background: rgba(69, 227, 255, 0.16);
    }
    .choice.incorrect {
      border-color: rgba(161, 99, 247, 0.55);
      background: rgba(161, 99, 247, 0.16);
    }
    .choice.revealed-correct {
      border-color: rgba(255, 245, 130, 0.38);
      box-shadow: inset 0 0 0 1px rgba(255, 245, 130, 0.12);
    }
    .study-note {
      min-height: 1.2rem;
      color: var(--muted);
      font-size: 0.92rem;
    }
    .study-note.correct {
      color: var(--success);
    }
    .study-note.incorrect {
      color: var(--danger);
    }
    img {
      max-width: 100%;
      height: auto;
      border-radius: 18px;
      border: 1px solid var(--border);
      background: rgba(35, 47, 66, 0.96);
      display: block;
      box-shadow: var(--shadow-soft);
    }
    .answer-shell {
      border-top: 1px dashed rgba(149, 180, 221, 0.34);
      padding-top: 1rem;
    }
    .answer-toggle {
      width: 100%;
      appearance: none;
      border: 1px solid var(--border);
      border-radius: 16px;
      background: linear-gradient(180deg, rgba(89, 110, 151, 0.98), rgba(65, 84, 117, 0.94));
      color: var(--heading);
      font: inherit;
      font-weight: 750;
      font-size: 1rem;
      text-align: left;
      padding: 1rem 1.1rem;
      cursor: pointer;
      min-height: 62px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
      transition: transform 160ms ease, border-color 160ms ease, background-color 160ms ease;
    }
    .answer-toggle:hover {
      transform: translateY(-1px);
      border-color: rgba(69, 227, 255, 0.4);
      background: linear-gradient(180deg, rgba(111, 136, 252, 1), rgba(77, 98, 136, 0.98));
    }
    .answer-toggle:focus-visible,
    .choice:focus-visible,
    .toolbar a:focus-visible,
    .toolbar button:focus-visible {
      outline: 2px solid rgba(69, 227, 255, 0.7);
      outline-offset: 2px;
    }
    .answer-chevron {
      flex: 0 0 auto;
      font-size: 1.15rem;
      color: var(--accent-strong);
      transition: transform 240ms ease;
    }
    .answer-panel {
      display: grid;
      grid-template-rows: 0fr;
      transition: grid-template-rows 320ms ease, opacity 220ms ease, margin-top 220ms ease;
      opacity: 0;
      margin-top: 0;
    }
    .answer-panel.open {
      grid-template-rows: 1fr;
      opacity: 1;
      margin-top: 0.9rem;
    }
    .answer-panel-inner {
      overflow: hidden;
    }
    .answer-block {
      display: grid;
      gap: 0.75rem;
      padding: 1rem;
      border: 1px solid var(--border);
      border-radius: 16px;
      background: linear-gradient(180deg, rgba(55, 72, 100, 0.98), rgba(41, 54, 76, 0.96));
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
      .toolbar a, .toolbar button, .card, .answer-toggle, .answer-panel, .answer-chevron, .choice {
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
      <div class="hero-stats">
        <div class="hero-stat"><strong>{{ flashcards|length }}</strong><span>Total Cards</span></div>
        <div class="hero-stat"><strong id="mastered-count">0</strong><span>Mastered</span></div>
        <div class="hero-stat"><strong id="needs-review-count">0</strong><span>Needs Review</span></div>
      </div>
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
            <div class="content question-text">{{ flashcard.question }}</div>
            {% if flashcard.choices %}
            <div class="study-note" data-study-note="q{{ flashcard.number }}"></div>
            <div class="choices" role="list" aria-label="Answer choices for question {{ flashcard.number }}">
              {% for label, text in flashcard.choices.items() %}
              <button class="choice" type="button" role="listitem" data-card-id="q{{ flashcard.number }}" data-choice="{{ label }}" data-correct="{{ flashcard.correct_answer_label or '' }}">
                <span class="choice-label">{{ label }}:</span>{{ text }}
              </button>
              {% endfor %}
            </div>
            {% endif %}
            {% for image_name in image_names(flashcard) %}
            <img src="media/{{ image_name }}" alt="Question {{ flashcard.number }} image">
            {% endfor %}
          </section>
          <section class="answer-shell">
            <button class="answer-toggle" type="button" aria-expanded="false" aria-controls="answer-panel-q{{ flashcard.number }}">
              <span>Show answer and feedback</span>
              <span class="answer-chevron">+</span>
            </button>
            <div class="answer-panel" id="answer-panel-q{{ flashcard.number }}">
              <div class="answer-panel-inner">
                <div class="answer-block">
                  <div><span class="answer-title">Answer:</span> {{ flashcard.answer or "Unavailable" }}</div>
                  <div class="content"><span class="answer-title">Feedback:</span><br>{{ flashcard.feedback }}</div>
                </div>
              </div>
            </div>
          </section>
        </div>
      </article>
      {% endfor %}
    </section>
  </main>
  <script>
    const answerToggles = Array.from(document.querySelectorAll(".answer-toggle"));
    const answerPanels = Array.from(document.querySelectorAll(".answer-panel"));
    const storageKey = "flashcard-study-state:" + window.location.pathname;
    const masteredCount = document.getElementById("mastered-count");
    const needsReviewCount = document.getElementById("needs-review-count");

    function setPanelState(toggle, open) {
      const panel = toggle.nextElementSibling;
      const chevron = toggle.querySelector(".answer-chevron");
      toggle.setAttribute("aria-expanded", String(open));
      panel.classList.toggle("open", open);
      chevron.textContent = open ? "−" : "+";
      chevron.style.transform = open ? "rotate(180deg)" : "rotate(0deg)";
    }

    answerToggles.forEach((toggle) => {
      toggle.addEventListener("click", () => {
        const isOpen = toggle.getAttribute("aria-expanded") === "true";
        setPanelState(toggle, !isOpen);
      });
    });

    document.getElementById("open-all").addEventListener("click", () => {
      answerToggles.forEach((toggle) => setPanelState(toggle, true));
    });

    document.getElementById("close-all").addEventListener("click", () => {
      answerToggles.forEach((toggle) => setPanelState(toggle, false));
    });

    function normalizeState(rawState) {
      const nextState = {};
      Object.keys(rawState || {}).forEach((key) => {
        const value = rawState[key];
        if (typeof value === "string") {
          nextState[key] = { status: value, selectedChoice: null };
        } else if (value && typeof value === "object") {
          nextState[key] = {
            status: value.status || null,
            selectedChoice: value.selectedChoice || null,
          };
        }
      });
      return nextState;
    }

    function loadStudyState() {
      try {
        return normalizeState(JSON.parse(localStorage.getItem(storageKey) || "{}"));
      } catch (error) {
        return {};
      }
    }

    function saveStudyState(state) {
      localStorage.setItem(storageKey, JSON.stringify(state));
    }

    function updateCounts(state) {
      const values = Object.values(state);
      const mastered = values.filter((value) => value && value.status === "correct").length;
      const review = values.filter((value) => value && value.status === "incorrect").length;
      masteredCount.textContent = String(mastered);
      needsReviewCount.textContent = String(review);
    }

    function renderChoiceState(cardId, state) {
      const group = document.querySelectorAll('.choice[data-card-id="' + cardId + '"]');
      if (!group.length) {
        return;
      }
      const selectedChoice = state && state.selectedChoice ? state.selectedChoice : null;
      const correctChoice = group[0].getAttribute("data-correct");
      group.forEach((item) => {
        item.classList.remove("correct", "incorrect", "revealed-correct");
        const itemChoice = item.getAttribute("data-choice");
        if (!selectedChoice) {
          return;
        }
        if (itemChoice === selectedChoice) {
          item.classList.add(selectedChoice === correctChoice ? "correct" : "incorrect");
        }
        if (selectedChoice !== correctChoice && itemChoice === correctChoice) {
          item.classList.add("revealed-correct");
        }
      });
    }

    function applyStudyState(state) {
      document.querySelectorAll("[data-study-note]").forEach((node) => {
        const cardId = node.getAttribute("data-study-note");
        const note = document.querySelector('[data-study-note="' + cardId + '"]');
        const current = state[cardId] || { status: null, selectedChoice: null };
        if (note) {
          if (current.selectedChoice && current.status === "correct") {
            note.textContent = "Correct. Saved on this device.";
          } else if (current.selectedChoice && current.status === "incorrect") {
            note.textContent = "Incorrect. The correct option is highlighted.";
          } else {
            note.textContent = "Choose an answer to track your progress.";
          }
          note.className = "study-note" + (current.status ? " " + current.status : "");
        }
        renderChoiceState(cardId, current);
      });
      updateCounts(state);
    }

    const studyState = loadStudyState();
    applyStudyState(studyState);

    document.querySelectorAll(".choice").forEach((button) => {
      button.addEventListener("click", () => {
        const cardId = button.getAttribute("data-card-id");
        const correct = button.getAttribute("data-correct");
        const choice = button.getAttribute("data-choice");
        if (!correct) {
          return;
        }
        studyState[cardId] = {
          status: choice === correct ? "correct" : "incorrect",
          selectedChoice: choice,
        };
        saveStudyState(studyState);
        applyStudyState(studyState);
      });
    });
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
      color: #ffffff;
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
      color: #d9e6fb;
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
    .item a:hover {
      color: #b4f0eb;
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
