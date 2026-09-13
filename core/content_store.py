"""Persistent user-created lessons and keyboard layouts."""

from __future__ import annotations

import json
import csv
import re
from pathlib import Path

from core.key_mapping import BUILTIN_LAYOUT_NAME
from core.lesson_loader import Lesson


def load_user_lessons(path: Path) -> list[Lesson]:
    """Load optional user-created lessons; invalid entries are ignored."""
    if not path.is_file():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return []
    if not isinstance(payload, list):
        return []
    return [
        {"title": str(item["title"]).strip(), "text": str(item["text"]).strip()}
        for item in payload
        if isinstance(item, dict) and str(item.get("title", "")).strip()
        and str(item.get("text", "")).strip()
    ]


def add_user_lesson(path: Path, title: str, text: str) -> Lesson:
    """Append and atomically persist a lesson."""
    lesson = {"title": title.strip(), "text": text.strip()}
    if not lesson["title"] or not lesson["text"]:
        raise ValueError("A title and lesson text are required")
    lessons = load_user_lessons(path)
    lessons.append(lesson)
    _write_json(path, lessons)
    return lesson


def add_user_lessons(path: Path, new_lessons: list[Lesson]) -> list[Lesson]:
    """Validate and persist several imported lessons in one atomic update."""
    cleaned = [
        {"title": str(item.get("title", "")).strip(),
         "text": str(item.get("text", "")).strip()}
        for item in new_lessons
    ]
    if not cleaned or any(not item["title"] or not item["text"] for item in cleaned):
        raise ValueError("Every lesson needs a title and practice text")
    lessons = load_user_lessons(path)
    lessons.extend(cleaned)
    _write_json(path, lessons)
    return cleaned


def update_user_lesson(path: Path, index: int, title: str, text: str) -> Lesson:
    """Replace one user-created lesson and persist the change."""
    lessons = load_user_lessons(path)
    if not 0 <= index < len(lessons):
        raise IndexError("The selected lesson no longer exists")
    lesson = {"title": title.strip(), "text": text.strip()}
    if not lesson["title"] or not lesson["text"]:
        raise ValueError("A title and lesson text are required")
    lessons[index] = lesson
    _write_json(path, lessons)
    return lesson


def delete_user_lesson(path: Path, index: int) -> Lesson:
    """Delete one user-created lesson and return the removed record."""
    lessons = load_user_lessons(path)
    if not 0 <= index < len(lessons):
        raise IndexError("The selected lesson no longer exists")
    removed = lessons.pop(index)
    _write_json(path, lessons)
    return removed


def import_lessons(path: Path) -> list[Lesson]:
    """Read lesson records from JSON or a header-based UTF-8 CSV file."""
    suffix = path.suffix.lower()
    if suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        records = payload if isinstance(payload, list) else [payload]
    elif suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            records = list(csv.DictReader(handle))
    else:
        raise ValueError("Choose a .json or .csv lesson file")
    if not all(isinstance(item, dict) for item in records):
        raise ValueError("Lesson import must contain objects or CSV rows")
    lessons = [
        {"title": str(item.get("title", "")).strip(),
         "text": str(item.get("text", "")).strip()}
        for item in records
        if str(item.get("title", "")).strip() or str(item.get("text", "")).strip()
    ]
    if not lessons or any(not item["title"] or not item["text"] for item in lessons):
        raise ValueError("Every imported lesson needs title and text fields")
    return lessons


def save_keyboard_layout(directory: Path, name: str,
                         bindings: dict[str, dict[str, str]]) -> Path:
    """Save a keyboard definition discoverable by the existing layout loader."""
    clean_name = name.strip()
    if not clean_name:
        raise ValueError("A layout name is required")
    if clean_name.casefold() in {"pa-o", BUILTIN_LAYOUT_NAME.casefold()}:
        raise ValueError(
            f"{BUILTIN_LAYOUT_NAME} is the built-in layout; choose a different name"
        )
    slug = re.sub(r"[^a-z0-9]+", "-", clean_name.lower()).strip("-") or "custom-layout"
    path = directory / f"{slug}.json"
    if path.is_file():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
            existing_name = str(existing.get("name", "")).strip()
        except (OSError, UnicodeError, json.JSONDecodeError, AttributeError):
            existing_name = ""
        if existing_name and existing_name.casefold() != clean_name.casefold():
            raise ValueError(f"The filename is already used by layout {existing_name!r}")
    _write_json(path, {"name": clean_name, "bindings": bindings})
    return path


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)
