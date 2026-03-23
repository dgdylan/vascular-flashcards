from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class ImageAsset:
    page_number: int
    xref: int | None
    bbox: tuple[float, float, float, float]
    ext: str
    data: bytes
    width: float
    height: float
    area: float
    saved_name: str | None = None

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload.pop("data", None)
        return payload


@dataclass
class TextBlock:
    page_number: int
    bbox: tuple[float, float, float, float]
    text: str
    raw_lines: list[str]


@dataclass
class QuestionBlock:
    number: int
    source_pdf: Path
    raw_text: str
    text_blocks: list[TextBlock]
    page_numbers: list[int]
    start_page: int
    end_page: int
    bbox: tuple[float, float, float, float]
    points_earned: float | None = None
    points_possible: float | None = None
    images: list[ImageAsset] = field(default_factory=list)


@dataclass
class Flashcard:
    number: int
    question: str
    answer: str
    feedback: str
    source_pdf: Path
    choices: dict[str, str] = field(default_factory=dict)
    user_answer: str | None = None
    correct_answer_label: str | None = None
    images: list[ImageAsset] = field(default_factory=list)
    page_numbers: list[int] = field(default_factory=list)
    points_earned: float | None = None
    points_possible: float | None = None
    raw_text: str = ""

    @property
    def is_missed(self) -> bool:
        if self.points_earned is not None and self.points_possible is not None:
            return self.points_earned < self.points_possible
        if self.correct_answer_label and self.user_answer:
            return self.correct_answer_label != self.user_answer
        return False

    def to_dict(self) -> dict:
        return {
            "number": self.number,
            "question": self.question,
            "answer": self.answer,
            "feedback": self.feedback,
            "choices": self.choices,
            "user_answer": self.user_answer,
            "correct_answer_label": self.correct_answer_label,
            "images": [image.to_dict() for image in self.images],
            "page_numbers": self.page_numbers,
            "points_earned": self.points_earned,
            "points_possible": self.points_possible,
            "is_missed": self.is_missed,
            "raw_text": self.raw_text,
        }
