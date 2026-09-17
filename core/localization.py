"""JSON-backed application localization with safe English fallbacks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ASCII_TO_PAO_DIGITS = str.maketrans("0123456789", "𑛐𑛑𑛒𑛓𑛔𑛕𑛖𑛗𑛘𑛙")


class Localizer:
    """Discover locales and translate dotted keys from editable JSON files."""

    def __init__(self, directory: Path, default: str = "en") -> None:
        self.directory = directory
        self.default = default
        self.catalogs: dict[str, dict[str, Any]] = {}
        self.names: dict[str, str] = {}
        self.current = default
        self.reload()

    def reload(self) -> None:
        self.catalogs.clear()
        self.names.clear()
        for path in sorted(self.directory.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                code = str(data.get("code", path.stem))
                self.catalogs[code] = data
                self.names[code] = str(data.get("name", code))
            except (OSError, ValueError, TypeError):
                continue
        if self.current not in self.catalogs:
            self.current = self.default if self.default in self.catalogs else next(iter(self.catalogs), "en")

    def set_language(self, code: str) -> None:
        if code in self.catalogs:
            self.current = code

    def text(self, message_key: str, **values: object) -> str:
        value = self._lookup(self.catalogs.get(self.current, {}), message_key)
        if value is None:
            value = self._lookup(self.catalogs.get(self.default, {}), message_key)
        result = str(value if value is not None else message_key)
        try:
            result = result.format(**values)
        except (KeyError, ValueError):
            pass
        return self.localize_digits(result)

    def localize_digits(self, value: str) -> str:
        """Render ASCII digits in the active locale's numeral system.

        Pa-O uses the Myanmar Pa-O digits in the U+116D0 block. Keeping this
        formatting at the localization boundary leaves lesson text and typing
        input untouched while making dynamic UI values consistent.
        """
        catalog = self.catalogs.get(self.current, {})
        if catalog.get("numbering_system") == "pao":
            return value.translate(ASCII_TO_PAO_DIGITS)
        return value

    @staticmethod
    def _lookup(catalog: dict[str, Any], key: str) -> object | None:
        value: object = catalog
        for part in key.split("."):
            if not isinstance(value, dict) or part not in value:
                return None
            value = value[part]
        return value
