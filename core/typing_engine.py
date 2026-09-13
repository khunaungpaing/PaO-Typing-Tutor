"""Stateful typing lesson engine, independent of the GUI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
import unicodedata


@dataclass(frozen=True)
class CharacterResult:
    """Validation result for one entered character."""

    index: int
    expected: str
    actual: str
    correct: bool


class TypingEngine:
    """Compare typed input with a target and retain current results."""

    def __init__(self, target: str = "") -> None:
        self.target = target
        self.typed = ""
        self.results: List[CharacterResult] = []

    def reset(self, target: str) -> None:
        """Start a new target lesson."""
        self.target = unicodedata.normalize("NFC", target)
        self.typed = ""
        self.results = []

    def update(self, typed: str) -> List[CharacterResult]:
        """Validate NFC Unicode input while preserving OpenType mark sequences."""
        self.typed = unicodedata.normalize("NFC", typed)
        self.results = [
            CharacterResult(i, self.target[i] if i < len(self.target) else "", char,
                            i < len(self.target) and char == self.target[i])
            for i, char in enumerate(self.typed)
        ]
        return self.results

    @property
    def correct_count(self) -> int:
        return sum(result.correct for result in self.results)

    @property
    def errors(self) -> List[CharacterResult]:
        return [result for result in self.results if not result.correct]

    @property
    def complete(self) -> bool:
        return len(self.typed) >= len(self.target) and self.typed == self.target

    @property
    def next_character(self) -> Optional[str]:
        index = len(self.typed)
        return self.target[index] if index < len(self.target) else None
