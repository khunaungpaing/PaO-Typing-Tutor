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

        def _is_correct(expected: str, actual: str) -> bool:
            if expected == actual:
                return True
            equivs = ({"\u108F", "\U000116E6"}, {"\u105E", "္လ"}, {"\u108B", "ႋ"})
            return any(expected in eq and actual in eq for eq in equivs)

        self.results = [
            CharacterResult(i, self.target[i] if i < len(self.target) else "", char,
                            i < len(self.target) and _is_correct(self.target[i], char))
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
        """Finish once the learner reaches the end, even with mistakes.

        Requiring an exact match leaves a learner stuck when an invisible
        character such as a space is wrong. The UI presents the mistakes in
        the completion review instead, where they can restart and retry.
        """
        return len(self.typed) >= len(self.target)

    @property
    def next_character(self) -> Optional[str]:
        index = len(self.typed)
        return self.target[index] if index < len(self.target) else None
