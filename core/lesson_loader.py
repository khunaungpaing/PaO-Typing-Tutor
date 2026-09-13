"""Lesson loading and validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Union

Lesson = Dict[str, str]

DEFAULT_LESSONS: List[Lesson] = [
    {"title": "အခန်ꩻ ၁ — မိတ်ဆက်", "text": "ခွေသွဉ်းနဝ်ꩻ ပအိုဝ်ႏလိုꩻမျိုꩻသွူ။"},
    {"title": "အခန်ꩻ ၂ — လွူꩻလိတ်", "text": "လွူꩻလိတ်ပအိုဝ်ႏ ကဲဉ်းအာအာနဝ်ꩻသွူ။"},
    {"title": "အခန်ꩻ ၃ — အုံအဝ်ႏ", "text": "နီသွဉ်းဖုံႏ အုံအဝ်ႏဟဝ်ဒျာႏသွူ။"},
]


class LessonLoader:
    """Load lessons from JSON, falling back to safe built-in content."""

    def __init__(self, path: Union[Path, str]) -> None:
        self.path = Path(path)
        self.last_warning: Optional[str] = None

    def load(self) -> List[Lesson]:
        """Return validated lessons and record a readable warning on failure."""
        try:
            with self.path.open("r", encoding="utf-8") as handle:
                raw = json.load(handle)
            if not isinstance(raw, list):
                raise ValueError("top-level JSON value must be a list")

            lessons: List[Lesson] = []
            for index, item in enumerate(raw, start=1):
                if not isinstance(item, dict) or not isinstance(item.get("text"), str):
                    raise ValueError(f"lesson {index} must contain a string 'text'")
                text = item["text"].strip()
                if not text:
                    raise ValueError(f"lesson {index} has empty text")
                title = item.get("title", f"Lesson {index}")
                lessons.append({"title": str(title), "text": text})
            if not lessons:
                raise ValueError("lesson list is empty")
            return lessons
        except (OSError, json.JSONDecodeError, UnicodeError, ValueError) as exc:
            self.last_warning = f"Could not load {self.path.name} ({exc}). Using built-in lessons."
            return [lesson.copy() for lesson in DEFAULT_LESSONS]
