"""
Vanta - Translation Loader
Handles switching between English (LTR) and Persian/Farsi (RTL).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

# Supported locales
SUPPORTED_LOCALES = ("en", "fa")
DEFAULT_LOCALE = "en"
TRANSLATIONS_DIR = Path(__file__).parent / "translations"


class TranslationLoader:
    """Loads and manages translations for i18n support."""

    def __init__(self) -> None:
        self._translations: dict[str, dict[str, str]] = {}
        self._current_locale: str = DEFAULT_LOCALE
        self._load_all()

    def _load_all(self) -> None:
        """Load all translation files from the translations directory."""
        for locale in SUPPORTED_LOCALES:
            file_path = TRANSLATIONS_DIR / f"{locale}.json"
            if file_path.exists():
                try:
                    with open(file_path, encoding="utf-8") as f:
                        self._translations[locale] = json.load(f)
                except (json.JSONDecodeError, OSError):
                    self._translations[locale] = {}

    def get(self, key: str, locale: str | None = None) -> str:
        """Get translated string for key. Falls back to key if not found."""
        loc = locale or self._current_locale
        translations = self._translations.get(loc, {})
        return translations.get(key, self._translations.get(DEFAULT_LOCALE, {}).get(key, key))

    def set_locale(self, locale: str) -> None:
        """Set the current locale."""
        if locale in SUPPORTED_LOCALES:
            self._current_locale = locale

    @property
    def locale(self) -> str:
        """Current locale."""
        return self._current_locale

    @property
    def is_rtl(self) -> bool:
        """Whether current locale uses RTL (e.g., Persian)."""
        return self._current_locale == "fa"
