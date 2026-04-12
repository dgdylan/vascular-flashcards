from __future__ import annotations

import re
from collections import Counter

from flashcards_builder.models import Flashcard


STOPWORDS = {
    "a",
    "about",
    "after",
    "all",
    "also",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "because",
    "before",
    "both",
    "but",
    "by",
    "can",
    "correct",
    "describe",
    "demonstrates",
    "during",
    "each",
    "exam",
    "feedback",
    "flow",
    "for",
    "following",
    "from",
    "have",
    "how",
    "if",
    "in",
    "into",
    "is",
    "it",
    "its",
    "leg",
    "most",
    "normal",
    "not",
    "of",
    "on",
    "or",
    "patient",
    "question",
    "review",
    "should",
    "shows",
    "that",
    "the",
    "their",
    "there",
    "this",
    "to",
    "used",
    "using",
    "vessel",
    "was",
    "what",
    "which",
    "with",
}


def build_research_brief(flashcard: Flashcard) -> dict:
    feedback_sentences = split_sentences(flashcard.feedback)
    answer_text = flashcard.answer or "Unavailable"
    primary_explanation = feedback_sentences[0] if feedback_sentences else answer_text
    secondary_explanation = feedback_sentences[1] if len(feedback_sentences) > 1 else ""

    question_type = classify_question(flashcard)
    focus_terms = extract_focus_terms(flashcard, limit=4)

    if secondary_explanation:
        takeaway = secondary_explanation
    elif len(feedback_sentences) > 1:
        takeaway = " ".join(feedback_sentences[1:2])
    else:
        takeaway = f"Anchor this to the correct answer: {answer_text}."

    return {
        "question_type": question_type,
        "overview": primary_explanation or answer_text,
        "takeaway": takeaway,
        "focus_terms": focus_terms,
        "self_checks": build_self_checks(flashcard, question_type, focus_terms),
    }


def split_sentences(text: str) -> list[str]:
    cleaned = " ".join(text.split())
    if not cleaned:
        return []
    pieces = re.split(r"(?<=[.!?])\s+", cleaned)
    return [piece.strip() for piece in pieces if piece.strip()]


def extract_focus_terms(flashcard: Flashcard, *, limit: int) -> list[str]:
    corpus = " ".join(
        part
        for part in (
            flashcard.question,
            flashcard.answer,
            flashcard.feedback,
        )
        if part
    ).lower()
    tokens = re.findall(r"[a-z0-9%'/+-]{3,}", corpus)
    filtered = [token for token in tokens if token not in STOPWORDS and not token.isdigit()]
    ranked = Counter(filtered).most_common()

    focus_terms: list[str] = []
    for token, _count in ranked:
        label = token.upper() if token.isupper() else token
        if label not in focus_terms:
            focus_terms.append(label)
        if len(focus_terms) >= limit:
            break
    return focus_terms


def classify_question(flashcard: Flashcard) -> str:
    text = f"{flashcard.question} {flashcard.feedback}".lower()
    if any(word in text for word in ("calculate", "ratio", "abi", "velocity", "equation")):
        return "Calculation / relationship"
    if any(word in text for word in ("waveform", "doppler", "pvr", "ppg", "spectral")):
        return "Waveform interpretation"
    if any(word in text for word in ("anatomy", "artery", "vein", "ivc", "aorta", "renal", "portal")):
        return "Anatomy / vessel ID"
    if any(word in text for word in ("normal", "abnormal", "expected", "change")):
        return "Concept recognition"
    return "Core review concept"


def build_self_checks(flashcard: Flashcard, question_type: str, focus_terms: list[str]) -> list[str]:
    prompts = [
        f"Can I explain in one sentence why {flashcard.answer or 'the correct answer'} is right?",
        f"What clue in the question makes this a {question_type.lower()} problem?",
    ]

    if focus_terms:
        prompts.append(f"Could I define or recognize these terms without notes: {', '.join(focus_terms)}?")
    else:
        prompts.append("Could I answer this again tomorrow without looking at the feedback?")
    return prompts
