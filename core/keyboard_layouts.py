"""Discovery and activation of extensible keyboard-layout JSON files."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from core.key_mapping import (
    BUILTIN_LAYOUT_NAME, DEFAULT_PAO_KEY_MAP, PAO_KEY_MAP, PHYSICAL_LABELS,
)


@dataclass(frozen=True)
class KeyboardLayout:
    """A named physical-key to Unicode-output mapping."""

    name: str
    mapping: dict[int, dict[str, str]]


def discover_layouts(directory: Path) -> tuple[list[KeyboardLayout], list[str]]:
    """Load valid JSON layouts while retaining Kham Dom as the built-in default."""
    layouts = [
        KeyboardLayout(
            BUILTIN_LAYOUT_NAME,
            {key: value.copy() for key, value in DEFAULT_PAO_KEY_MAP.items()},
        )
    ]
    warnings: list[str] = []
    seen_names = {"pa-o", BUILTIN_LAYOUT_NAME.casefold()}
    label_to_key = {label: key for key, label in PHYSICAL_LABELS.items()}
    for path in sorted(directory.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            name = payload["name"]
            bindings = payload["bindings"]
            if not isinstance(name, str) or not isinstance(bindings, dict):
                raise ValueError("name and bindings are required")
            name = name.strip()
            if not name:
                raise ValueError("layout name cannot be empty")
            normalized_name = name.casefold()
            if normalized_name in seen_names:
                warnings.append(f"Skipped duplicate keyboard layout {name!r} from {path.name}")
                continue
            mapping = {key: value.copy() for key, value in DEFAULT_PAO_KEY_MAP.items()}
            for label, states in bindings.items():
                if label not in label_to_key or not isinstance(states, dict):
                    raise ValueError(f"invalid physical key {label!r}")
                normal, shift = states.get("normal"), states.get("shift")
                if not isinstance(normal, str) or not isinstance(shift, str):
                    raise ValueError(f"{label!r} needs string normal and shift outputs")
                mapping[label_to_key[label]] = {"normal": normal, "shift": shift}
            layouts.append(KeyboardLayout(name, mapping))
            seen_names.add(normalized_name)
        except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            warnings.append(f"Could not load keyboard {path.name}: {exc}")
    return layouts, warnings


def activate_layout(layout: KeyboardLayout) -> None:
    """Activate a layout for input translation and target-key lookup."""
    PAO_KEY_MAP.clear()
    PAO_KEY_MAP.update({key: value.copy() for key, value in layout.mapping.items()})
