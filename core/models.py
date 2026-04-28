from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any


@dataclass
class SourceRef:
    filename: str
    sheet: str
    subcategory: str | None = None


@dataclass
class WordEntry:
    word: str
    meaning: str | None = None
    example: str | None = None
    pos: str | None = None
    synonyms: list[str] = field(default_factory=list)
    antonyms: list[str] = field(default_factory=list)
    mnemonics: list[str] = field(default_factory=list)
    sources: list[SourceRef] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "word": self.word,
            "meaning": self.meaning,
            "example": self.example,
            "pos": self.pos,
            "synonyms": self.synonyms,
            "antonyms": self.antonyms,
            "mnemonics": self.mnemonics,
            "sources": [source.__dict__ for source in self.sources],
            "tags": self.tags,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "WordEntry":
        sources = [SourceRef(**source) for source in data.get("sources", [])]
        return WordEntry(
            word=data["word"],
            meaning=data.get("meaning"),
            example=data.get("example"),
            pos=data.get("pos"),
            synonyms=list(data.get("synonyms", [])),
            antonyms=list(data.get("antonyms", [])),
            mnemonics=list(data.get("mnemonics", [])),
            sources=sources,
            tags=list(data.get("tags", [])),
        )


@dataclass
class ReviewState:
    word: str
    due_date: date
    interval_days: int = 0
    ease_factor: float = 2.5
    last_review: date | None = None
    review_count: int = 0
    lapse_count: int = 0
    correct_count: int = 0
    incorrect_count: int = 0

    def accuracy(self) -> float:
        total = self.correct_count + self.incorrect_count
        if total == 0:
            return 0.0
        return self.correct_count / total

    def to_dict(self) -> dict[str, Any]:
        return {
            "word": self.word,
            "due_date": self.due_date.isoformat(),
            "interval_days": self.interval_days,
            "ease_factor": self.ease_factor,
            "last_review": self.last_review.isoformat() if self.last_review else None,
            "review_count": self.review_count,
            "lapse_count": self.lapse_count,
            "correct_count": self.correct_count,
            "incorrect_count": self.incorrect_count,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "ReviewState":
        return ReviewState(
            word=data["word"],
            due_date=date.fromisoformat(data["due_date"]),
            interval_days=int(data.get("interval_days", 0)),
            ease_factor=float(data.get("ease_factor", 2.5)),
            last_review=date.fromisoformat(data["last_review"]) if data.get("last_review") else None,
            review_count=int(data.get("review_count", 0)),
            lapse_count=int(data.get("lapse_count", 0)),
            correct_count=int(data.get("correct_count", 0)),
            incorrect_count=int(data.get("incorrect_count", 0)),
        )


@dataclass
class DeckReviewState:
    word_id: str
    state: str = "new"
    last_reviewed_at: datetime | None = None
    next_due_at: datetime | None = None
    interval_days: int = 0
    ease: float = 2.5
    reviews: int = 0
    lapses: int = 0
    last_outcome: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "word_id": self.word_id,
            "state": self.state,
            "last_reviewed_at": self.last_reviewed_at.isoformat() if self.last_reviewed_at else None,
            "next_due_at": self.next_due_at.isoformat() if self.next_due_at else None,
            "interval_days": self.interval_days,
            "ease": self.ease,
            "reviews": self.reviews,
            "lapses": self.lapses,
            "last_outcome": self.last_outcome,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "DeckReviewState":
        return DeckReviewState(
            word_id=str(data.get("word_id", "")),
            state=str(data.get("state", "new")),
            last_reviewed_at=datetime.fromisoformat(data["last_reviewed_at"])
            if data.get("last_reviewed_at")
            else None,
            next_due_at=datetime.fromisoformat(data["next_due_at"]) if data.get("next_due_at") else None,
            interval_days=int(data.get("interval_days", 0)),
            ease=float(data.get("ease", 2.5)),
            reviews=int(data.get("reviews", 0)),
            lapses=int(data.get("lapses", 0)),
            last_outcome=data.get("last_outcome"),
        )


@dataclass
class NormalizationReport:
    total_rows: int
    total_words: int
    deduped_words: int
    missing_meaning: int
    missing_example: int
    missing_pos: int
    missing_mnemonic: int
    missing_synonyms: int
    source_counts: dict[str, int]
    sheet_counts: dict[str, int]
    missing_files: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_rows": self.total_rows,
            "total_words": self.total_words,
            "deduped_words": self.deduped_words,
            "missing_meaning": self.missing_meaning,
            "missing_example": self.missing_example,
            "missing_pos": self.missing_pos,
            "missing_mnemonic": self.missing_mnemonic,
            "missing_synonyms": self.missing_synonyms,
            "source_counts": self.source_counts,
            "sheet_counts": self.sheet_counts,
            "missing_files": self.missing_files,
        }
