"""Typing performance calculations."""

from __future__ import annotations


class MetricsCalculator:
    """Stateless calculations for typing metrics."""

    @staticmethod
    def accuracy(correct_chars: int, total_typed: int) -> float:
        """Calculate typed-character accuracy as a percentage."""
        return (correct_chars / total_typed * 100.0) if total_typed else 100.0

    @staticmethod
    def cpm(correct_chars: int, elapsed_seconds: float) -> float:
        """Calculate correct characters per minute."""
        return (correct_chars * 60.0 / elapsed_seconds) if elapsed_seconds > 0 else 0.0

    @classmethod
    def wpm(cls, correct_chars: int, elapsed_seconds: float) -> float:
        """Calculate standard WPM using five correct characters per word."""
        return cls.cpm(correct_chars, elapsed_seconds) / 5.0
