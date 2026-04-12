from __future__ import annotations

import html
from collections import defaultdict
from pathlib import Path

from jinja2 import DictLoader, Environment, select_autoescape

from flashcards_builder.models import Flashcard
from flashcards_builder.research import build_research_brief
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
      color-scheme: light;
      --bg: #ffffff;
      --hero-a: #2f72a6;
      --hero-b: #5b9ace;
      --card: #ffffff;
      --card-soft: #f7fbfe;
      --ink: #153f66;
      --muted: #3f607e;
      --accent: #1aaebe;
      --accent-dark: #174f7f;
      --border: rgba(46, 110, 163, 0.14);
      --success: #2f9e61;
      --danger: #d94841;
      --shadow: 0 18px 40px rgba(35, 79, 127, 0.10);
      --shadow-soft: 0 8px 20px rgba(35, 79, 127, 0.06);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Avenir Next", "Segoe UI", "Helvetica Neue", sans-serif;
      background: #ffffff;
      color: var(--ink);
      min-height: 100vh;
    }
    .wrap {
      width: min(1120px, calc(100% - 2.25rem));
      margin: 0 auto;
      padding: 1rem 0 3.5rem;
    }
    .hero {
      position: relative;
      overflow: hidden;
      margin-bottom: 1.25rem;
      padding: clamp(1.4rem, 2.4vw, 2rem);
      border: 1px solid rgba(255,255,255,0.12);
      border-radius: 24px;
      background: linear-gradient(135deg, var(--hero-a), var(--hero-b));
      box-shadow: 0 22px 46px rgba(239, 227, 179, 0.35);
      animation: rise-in 520ms ease-out both;
    }
    .hero::after {
      content: "";
      position: absolute;
      right: -6%;
      bottom: -22%;
      width: 260px;
      aspect-ratio: 1;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(255,255,255,0.16), transparent 70%);
      pointer-events: none;
    }
    .eyebrow {
      margin: 0 0 0.8rem;
      color: rgba(255,255,255,0.84);
      font-size: 0.8rem;
      font-weight: 800;
      letter-spacing: 0.18em;
      text-transform: uppercase;
    }
    h1 {
      margin: 0;
      max-width: 11ch;
      color: #ffffff;
      font-size: clamp(2.2rem, 5vw, 4.1rem);
      line-height: 0.96;
      letter-spacing: -0.05em;
      text-wrap: balance;
    }
    .subhead {
      margin: 0.9rem 0 0;
      max-width: 50ch;
      color: rgba(255,255,255,0.86);
      font-size: clamp(1rem, 1.35vw, 1.1rem);
      line-height: 1.6;
    }
    .hero-row {
      display: flex;
      flex-wrap: wrap;
      align-items: flex-end;
      justify-content: space-between;
      gap: 1rem;
      margin-top: 1rem;
    }
    .hero-stats {
      display: flex;
      flex-wrap: wrap;
      gap: 0.75rem;
    }
    .hero-stat {
      min-width: 118px;
      padding: 0.72rem 0.95rem;
      border: 1px solid rgba(255,255,255,0.16);
      border-radius: 16px;
      background: rgba(255,255,255,0.10);
      color: #ffffff;
    }
    .hero-stat strong {
      display: block;
      font-size: 1rem;
    }
    .hero-stat span {
      display: block;
      margin-top: 0.18rem;
      color: rgba(255,255,255,0.74);
      font-size: 0.82rem;
      letter-spacing: 0.06em;
      text-transform: uppercase;
    }
    .toolbar {
      display: flex;
      flex-wrap: wrap;
      gap: 0.7rem;
    }
    .toolbar a, .toolbar button {
      border: 1px solid rgba(255,255,255,0.16);
      background: #ffffff;
      color: var(--accent-dark);
      border-radius: 999px;
      padding: 0.82rem 1.05rem;
      cursor: pointer;
      text-decoration: none;
      font: inherit;
      font-weight: 800;
      transition: transform 180ms ease, box-shadow 180ms ease;
    }
    .toolbar a:hover, .toolbar button:hover {
      transform: translateY(-1px);
      box-shadow: var(--shadow-soft);
    }
    .exam-timer {
      display: grid;
      gap: 0.55rem;
      min-width: min(100%, 320px);
      padding: 0.85rem 0.95rem;
      border: 1px solid rgba(255,255,255,0.16);
      border-radius: 16px;
      background: rgba(255,255,255,0.10);
      color: #ffffff;
    }
    .timer-label {
      color: rgba(255,255,255,0.74);
      font-size: 0.78rem;
      font-weight: 800;
      letter-spacing: 0.12em;
      text-transform: uppercase;
    }
    .timer-time {
      font-size: clamp(1.35rem, 2vw, 1.7rem);
      font-weight: 850;
      letter-spacing: 0.04em;
      line-height: 1;
    }
    .timer-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
    }
    .timer-actions button {
      border: 1px solid rgba(255,255,255,0.16);
      background: #ffffff;
      color: var(--accent-dark);
      border-radius: 999px;
      cursor: pointer;
      font: inherit;
      font-size: 0.88rem;
      font-weight: 800;
      padding: 0.58rem 0.78rem;
    }
    .timer-status {
      min-height: 1.1rem;
      color: rgba(255,255,255,0.76);
      font-size: 0.88rem;
    }
    .timer-expired .timer-time {
      color: #ffe4e4;
    }
    .cards {
      display: grid;
      gap: 1rem;
    }
    .card {
      background: var(--card);
      border: 1px solid rgba(86, 214, 227, 0.16);
      border-radius: 20px;
      box-shadow: 0 18px 40px rgba(239, 227, 179, 0.28);
      overflow: hidden;
      animation: rise-in 460ms ease-out both;
      transition: transform 200ms ease, box-shadow 200ms ease, border-color 200ms ease;
    }
    .card:hover {
      transform: translateY(-2px);
      border-color: rgba(86, 214, 227, 0.24);
      box-shadow: 0 20px 44px rgba(239, 227, 179, 0.32);
    }
    .card-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
      padding: 1rem 1.15rem;
      border-bottom: 1px solid rgba(86, 214, 227, 0.14);
      background: linear-gradient(180deg, #eef9fd, #f7fcfe);
    }
    .card-number {
      color: var(--accent-dark);
      font-size: 0.9rem;
      font-weight: 800;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }
    .pill {
      padding: 0.3rem 0.65rem;
      border-radius: 999px;
      background: rgba(86, 214, 227, 0.14);
      color: var(--accent-dark);
      font-size: 0.84rem;
      font-weight: 700;
    }
    .card-body {
      display: grid;
      gap: 1rem;
      padding: 1.15rem;
    }
    .card-side {
      display: grid;
      gap: 0.8rem;
    }
    .label {
      color: #174f7f;
      font-size: 0.78rem;
      font-weight: 800;
      letter-spacing: 0.1em;
      text-transform: uppercase;
    }
    .content {
      font-size: 1rem;
      line-height: 1.7;
      white-space: pre-wrap;
    }
    .question-text {
      color: #153f66;
      font-size: clamp(1.05rem, 1.35vw, 1.2rem);
      font-weight: 750;
      letter-spacing: -0.01em;
    }
    .study-note {
      min-height: 1.2rem;
      padding: 0 0.2rem;
      font-size: 0.92rem;
      color: var(--muted);
    }
    .study-note.correct {
      color: var(--success);
    }
    .study-note.incorrect {
      color: var(--danger);
    }
    .choice-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 0.75rem;
      flex-wrap: wrap;
    }
    .clear-answer {
      appearance: none;
      border: 1px solid rgba(46, 110, 163, 0.12);
      border-radius: 999px;
      background: #ffffff;
      color: var(--muted);
      cursor: pointer;
      font: inherit;
      font-size: 0.88rem;
      font-weight: 700;
      padding: 0.55rem 0.8rem;
      transition: transform 160ms ease, border-color 160ms ease, color 160ms ease;
    }
    .clear-answer:hover {
      transform: translateY(-1px);
      border-color: rgba(239, 131, 84, 0.22);
      color: var(--accent-dark);
    }
    .choices {
      display: grid;
      gap: 0.9rem;
      padding: 0.8rem;
      border: 1px solid rgba(86, 214, 227, 0.14);
      border-radius: 18px;
      background: var(--card-soft);
    }
    .choice {
      appearance: none;
      width: 100%;
      border: 1px solid rgba(46, 110, 163, 0.10);
      border-radius: 14px;
      background: #ffffff;
      color: #153f66;
      cursor: pointer;
      font: inherit;
      line-height: 1.55;
      padding: 1rem 1.05rem;
      text-align: left;
      transition: transform 160ms ease, border-color 160ms ease, background-color 160ms ease;
    }
    .choice:hover {
      transform: translateY(-1px);
      border-color: rgba(86, 214, 227, 0.28);
      background: #fcfeff;
    }
    .choice-label {
      color: #128fa0;
      font-weight: 800;
      margin-right: 0.3rem;
    }
    .choice.correct {
      border-color: rgba(47, 158, 97, 0.42);
      background: rgba(47, 158, 97, 0.10);
    }
    .choice.incorrect {
      border-color: rgba(217, 72, 65, 0.40);
      background: rgba(217, 72, 65, 0.10);
    }
    .choice.revealed-correct {
      border-color: rgba(47, 158, 97, 0.26);
      box-shadow: inset 0 0 0 1px rgba(47, 158, 97, 0.14);
    }
    img {
      display: block;
      max-width: 100%;
      height: auto;
      border: 1px solid rgba(86, 214, 227, 0.14);
      border-radius: 16px;
      background: #ffffff;
      box-shadow: var(--shadow-soft);
    }
    .answer-shell {
      border-top: 1px dashed rgba(46, 110, 163, 0.12);
      padding-top: 1rem;
    }
    .answer-toggle {
      appearance: none;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
      width: 100%;
      min-height: 60px;
      padding: 0.95rem 1.05rem;
      border: 1px solid rgba(86, 214, 227, 0.14);
      border-radius: 16px;
      background: linear-gradient(180deg, #ffffff, #fbfeff);
      color: var(--accent-dark);
      cursor: pointer;
      font: inherit;
      font-size: 1rem;
      font-weight: 750;
      text-align: left;
      transition: transform 160ms ease, border-color 160ms ease, background-color 160ms ease;
    }
    .answer-toggle:hover {
      transform: translateY(-1px);
      border-color: rgba(86, 214, 227, 0.22);
      background: linear-gradient(180deg, #ffffff, #f8fdff);
    }
    .answer-toggle:focus-visible,
    .choice:focus-visible,
    .toolbar a:focus-visible,
    .toolbar button:focus-visible {
      outline: 2px solid rgba(86, 214, 227, 0.32);
      outline-offset: 2px;
    }
    .answer-chevron {
      color: var(--accent);
      flex: 0 0 auto;
      font-size: 1.15rem;
      transition: transform 240ms ease;
    }
    .answer-panel {
      display: grid;
      grid-template-rows: 0fr;
      opacity: 0;
      margin-top: 0;
      transition: grid-template-rows 320ms ease, opacity 220ms ease, margin-top 220ms ease;
    }
    .answer-panel.open {
      grid-template-rows: 1fr;
      opacity: 1;
      margin-top: 0.85rem;
    }
    .answer-panel-inner {
      overflow: hidden;
    }
    .answer-block {
      display: grid;
      gap: 0.75rem;
      padding: 1rem;
      border: 1px solid rgba(86, 214, 227, 0.14);
      border-radius: 16px;
      background: var(--card-soft);
    }
    .research-block {
      display: grid;
      gap: 0.85rem;
      padding: 1rem;
      border: 1px solid rgba(46, 110, 163, 0.12);
      border-radius: 16px;
      background: #ffffff;
    }
    .research-grid {
      display: grid;
      gap: 0.85rem;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    }
    .research-card {
      padding: 0.9rem;
      border: 1px solid rgba(46, 110, 163, 0.10);
      border-radius: 14px;
      background: #fbfeff;
    }
    .research-title {
      margin: 0 0 0.45rem;
      color: var(--accent-dark);
      font-size: 0.84rem;
      font-weight: 800;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }
    .research-text {
      color: var(--ink);
      line-height: 1.6;
    }
    .research-tags {
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
    }
    .research-tag {
      padding: 0.42rem 0.7rem;
      border-radius: 999px;
      background: rgba(86, 214, 227, 0.12);
      color: var(--accent-dark);
      font-size: 0.85rem;
      font-weight: 700;
    }
    .research-checks {
      display: grid;
      gap: 0.55rem;
      margin: 0;
      padding-left: 1.1rem;
      color: var(--ink);
    }
    .answer-title {
      font-weight: 700;
    }
    @keyframes rise-in {
      from {
        opacity: 0;
        transform: translateY(14px);
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
    @media (max-width: 720px) {
      .wrap {
        width: min(100% - 1rem, 1120px);
        padding-top: 0.85rem;
      }
      .hero {
        padding: 1.1rem;
        border-radius: 18px;
      }
      .hero-row {
        align-items: stretch;
      }
      .toolbar {
        width: 100%;
      }
      .toolbar a, .toolbar button {
        width: 100%;
        justify-content: center;
        text-align: center;
      }
      .exam-timer {
        width: 100%;
      }
      .timer-actions button {
        flex: 1 1 120px;
      }
      .choice-row {
        align-items: stretch;
      }
      .clear-answer {
        width: 100%;
      }
      h1 {
        max-width: none;
      }
      .card-header, .card-body {
        padding: 1rem;
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
      <div class="hero-row">
        <div class="hero-stats">
          <div class="hero-stat"><strong>{{ flashcards|length }}</strong><span>Total Cards</span></div>
          <div class="hero-stat"><strong id="mastered-count">0</strong><span>Mastered</span></div>
          <div class="hero-stat"><strong id="needs-review-count">0</strong><span>Needs Review</span></div>
        </div>
        <div class="toolbar">
          <a href="../index.html">Back to index</a>
          <button type="button" id="open-all">Open all backs</button>
          <button type="button" id="close-all">Close all backs</button>
          <button type="button" id="clear-all-answers">Clear saved answers</button>
        </div>
        {% if is_mock_exam %}
        <div class="exam-timer" id="exam-timer" data-duration-seconds="10800">
          <div class="timer-label">Optional Exam Timer</div>
          <div class="timer-time" id="timer-display">03:00:00</div>
          <div class="timer-actions">
            <button type="button" id="timer-start">Start</button>
            <button type="button" id="timer-pause">Pause</button>
            <button type="button" id="timer-reset">Reset</button>
          </div>
          <div class="timer-status" id="timer-status">Timer is optional and saved on this device.</div>
        </div>
        {% endif %}
      </div>
    </section>
    <section class="cards">
      {% for flashcard in flashcards %}
      <article class="card" id="q{{ flashcard.number }}" style="animation-delay: {{ loop.index0 * 30 }}ms;">
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
            <div class="choice-row">
              <div class="label">Choices</div>
              <button class="clear-answer" type="button" data-clear-card="q{{ flashcard.number }}">Clear answer</button>
            </div>
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
                {% set research = research_for(flashcard) %}
                <div class="research-block">
                  <div class="label">Research & Study Guide</div>
                  <div class="research-grid">
                    <section class="research-card">
                      <h3 class="research-title">Question Type</h3>
                      <div class="research-text">{{ research.question_type }}</div>
                    </section>
                    <section class="research-card">
                      <h3 class="research-title">Core Idea</h3>
                      <div class="research-text">{{ research.overview }}</div>
                    </section>
                    <section class="research-card">
                      <h3 class="research-title">What To Remember</h3>
                      <div class="research-text">{{ research.takeaway }}</div>
                    </section>
                  </div>
                  {% if research.focus_terms %}
                  <section>
                    <h3 class="research-title">Focus Terms</h3>
                    <div class="research-tags">
                      {% for term in research.focus_terms %}
                      <span class="research-tag">{{ term }}</span>
                      {% endfor %}
                    </div>
                  </section>
                  {% endif %}
                  <section>
                    <h3 class="research-title">Self-Check</h3>
                    <ul class="research-checks">
                      {% for prompt in research.self_checks %}
                      <li>{{ prompt }}</li>
                      {% endfor %}
                    </ul>
                  </section>
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

    document.getElementById("clear-all-answers").addEventListener("click", () => {
      Object.keys(studyState).forEach((key) => delete studyState[key]);
      saveStudyState(studyState);
      applyStudyState(studyState);
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
      if (!group.length) return;
      const selectedChoice = state && state.selectedChoice ? state.selectedChoice : null;
      const correctChoice = group[0].getAttribute("data-correct");
      group.forEach((item) => {
        item.classList.remove("correct", "incorrect", "revealed-correct");
        const itemChoice = item.getAttribute("data-choice");
        if (!selectedChoice) return;
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
        const current = state[cardId] || { status: null, selectedChoice: null };
        if (current.selectedChoice && current.status === "correct") {
          node.textContent = "Correct.";
        } else if (current.selectedChoice && current.status === "incorrect") {
          node.textContent = "Incorrect. The correct option is highlighted.";
        } else {
          node.textContent = "";
        }
        node.className = "study-note" + (current.status ? " " + current.status : "");
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
        if (!correct) return;
        studyState[cardId] = {
          status: choice === correct ? "correct" : "incorrect",
          selectedChoice: choice,
        };
        saveStudyState(studyState);
        applyStudyState(studyState);
      });
    });

    document.querySelectorAll("[data-clear-card]").forEach((button) => {
      button.addEventListener("click", () => {
        const cardId = button.getAttribute("data-clear-card");
        delete studyState[cardId];
        saveStudyState(studyState);
        applyStudyState(studyState);
      });
    });

    const timerRoot = document.getElementById("exam-timer");
    if (timerRoot) {
      const timerKey = "flashcard-exam-timer:" + window.location.pathname;
      const durationSeconds = Number(timerRoot.getAttribute("data-duration-seconds") || "10800");
      const display = document.getElementById("timer-display");
      const status = document.getElementById("timer-status");
      const startButton = document.getElementById("timer-start");
      const pauseButton = document.getElementById("timer-pause");
      const resetButton = document.getElementById("timer-reset");
      let intervalId = null;

      function loadTimerState() {
        try {
          return JSON.parse(localStorage.getItem(timerKey) || "{}");
        } catch (error) {
          return {};
        }
      }

      function saveTimerState(state) {
        localStorage.setItem(timerKey, JSON.stringify(state));
      }

      function formatTime(totalSeconds) {
        const safeSeconds = Math.max(0, Math.floor(totalSeconds));
        const hours = String(Math.floor(safeSeconds / 3600)).padStart(2, "0");
        const minutes = String(Math.floor((safeSeconds % 3600) / 60)).padStart(2, "0");
        const seconds = String(safeSeconds % 60).padStart(2, "0");
        return hours + ":" + minutes + ":" + seconds;
      }

      function remainingSeconds(state) {
        if (!state.startedAt) {
          return durationSeconds;
        }
        if (state.pausedAt) {
          return Math.max(0, state.remainingAtPause ?? durationSeconds);
        }
        const elapsed = Math.floor((Date.now() - state.startedAt) / 1000);
        return Math.max(0, durationSeconds - elapsed);
      }

      function renderTimer() {
        const state = loadTimerState();
        const remaining = remainingSeconds(state);
        display.textContent = formatTime(remaining);
        timerRoot.classList.toggle("timer-expired", remaining === 0);
        if (remaining === 0 && state.startedAt) {
          status.textContent = "Time is up.";
          stopTicking();
        } else if (state.startedAt && state.pausedAt) {
          status.textContent = "Timer paused.";
        } else if (state.startedAt) {
          status.textContent = "Timer running.";
        } else {
          status.textContent = "Timer is optional and saved on this device.";
        }
      }

      function startTicking() {
        stopTicking();
        intervalId = window.setInterval(renderTimer, 1000);
      }

      function stopTicking() {
        if (intervalId !== null) {
          window.clearInterval(intervalId);
          intervalId = null;
        }
      }

      startButton.addEventListener("click", () => {
        const state = loadTimerState();
        const remaining = remainingSeconds(state);
        if (remaining <= 0) {
          return;
        }
        if (state.pausedAt) {
          saveTimerState({
            startedAt: Date.now() - ((durationSeconds - remaining) * 1000),
            pausedAt: null,
            remainingAtPause: null,
          });
        } else if (!state.startedAt) {
          saveTimerState({ startedAt: Date.now(), pausedAt: null, remainingAtPause: null });
        }
        renderTimer();
        startTicking();
      });

      pauseButton.addEventListener("click", () => {
        const state = loadTimerState();
        if (!state.startedAt || state.pausedAt) {
          return;
        }
        saveTimerState({
          startedAt: state.startedAt,
          pausedAt: Date.now(),
          remainingAtPause: remainingSeconds(state),
        });
        renderTimer();
        stopTicking();
      });

      resetButton.addEventListener("click", () => {
        localStorage.removeItem(timerKey);
        renderTimer();
        stopTicking();
      });

      renderTimer();
      if (loadTimerState().startedAt && !loadTimerState().pausedAt) {
        startTicking();
      }
    }
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
      --bg: #ffffff;
      --hero-a: #2f72a6;
      --hero-b: #5b9ace;
      --ink: #234f7f;
      --muted: #3f607e;
      --accent: #1aaebe;
      --accent-dark: #174f7f;
      --border: rgba(46, 110, 163, 0.14);
      --shadow: 0 18px 40px rgba(35, 79, 127, 0.10);
      --shadow-soft: 0 8px 20px rgba(35, 79, 127, 0.06);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Avenir Next", "Segoe UI", "Helvetica Neue", sans-serif;
      background: #ffffff;
      color: var(--ink);
    }
    .wrap {
      width: min(1120px, calc(100% - 2.25rem));
      margin: 0 auto;
      padding: 1rem 0 3.5rem;
    }
    .hero {
      margin-bottom: 1.4rem;
      padding: clamp(1.4rem, 2.4vw, 2rem);
      border: 1px solid rgba(255,255,255,0.12);
      border-radius: 24px;
      background: linear-gradient(135deg, var(--hero-a), var(--hero-b));
      box-shadow: 0 22px 46px rgba(239, 227, 179, 0.35);
      animation: rise-in 520ms ease-out both;
    }
    .eyebrow {
      margin: 0 0 0.8rem;
      color: rgba(255,255,255,0.84);
      font-size: 0.8rem;
      font-weight: 800;
      letter-spacing: 0.18em;
      text-transform: uppercase;
    }
    h1 {
      margin: 0;
      max-width: 9ch;
      color: #ffffff;
      font-size: clamp(2.3rem, 5vw, 4.2rem);
      line-height: 0.96;
      letter-spacing: -0.05em;
      text-wrap: balance;
    }
    p {
      max-width: 46ch;
      color: rgba(255,255,255,0.84);
      line-height: 1.65;
    }
    .group {
      margin-top: 1.8rem;
      padding-inline: 0.2rem;
    }
    .group h2 {
      margin-bottom: 0.75rem;
      color: #174f7f;
      font-size: 1.3rem;
      letter-spacing: -0.02em;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 1rem;
    }
    .item {
      background: #ffffff;
      border: 1px solid rgba(86, 214, 227, 0.16);
      border-radius: 18px;
      padding: 1rem;
      box-shadow: 0 18px 40px rgba(239, 227, 179, 0.28);
      animation: rise-in 460ms ease-out both;
      transition: transform 200ms ease, box-shadow 200ms ease, border-color 200ms ease;
    }
    .item:hover {
      transform: translateY(-2px);
      border-color: rgba(86, 214, 227, 0.24);
      box-shadow: 0 20px 44px rgba(239, 227, 179, 0.32);
    }
    .item a {
      color: #128fa0;
      text-decoration: none;
      font-size: 1.05rem;
      font-weight: 800;
    }
    .item a:first-child {
      color: #174f7f;
      font-size: 1.08rem;
    }
    .meta {
      margin-top: 0.45rem;
      color: var(--muted);
      font-size: 0.95rem;
    }
    @keyframes rise-in {
      from {
        opacity: 0;
        transform: translateY(14px);
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
    @media (max-width: 720px) {
      .wrap {
        width: min(100% - 1rem, 1120px);
        padding-top: 0.85rem;
      }
      .hero {
        padding: 1.1rem;
        border-radius: 18px;
      }
      h1 {
        max-width: none;
      }
      .grid {
        grid-template-columns: 1fr;
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
        <article class="item" style="animation-delay: {{ loop.index0 * 30 }}ms;">
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
    return template.render(
        title=title,
        flashcards=flashcards,
        image_names=image_names,
        research_for=build_research_brief,
        is_mock_exam=title.startswith("ARDMS Vascular Mock Registry Exam "),
    )


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
