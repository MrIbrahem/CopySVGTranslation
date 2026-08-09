"""
Module for stripping year patterns from title translations and merging them into mapping.new.
"""

from __future__ import annotations

import logging

from ..core.mapping import TranslationMapping

logger = logging.getLogger(__name__)


class YearPatternStripper:
    """
    Language-specific removal of `{year}` (and related suffixes/prefixes) from a single string.
    """

    GENERIC_SUFFIXES = [
        ", {year}",
        ",{year}",
        "، {year}",
        "،{year}",
    ]

    LANG_SPECIFIC = {
        "abr": {
            "suffixes": [", afe {year}"],
        },
        "ja": {
            "prefixes": ["{year}年の", "{year}年"],
            "suffixes": ["年{year}"],
        },
    }

    def __init__(self, lang: str, text: str) -> None:
        self.lang = lang
        self.text = text

    def run(self) -> str | None:
        if not self.text:
            return None

        if "{year}" not in self.text:
            return None

        # Check language-specific patterns first
        spec = self.LANG_SPECIFIC.get(self.lang)
        if spec:
            for prefix in spec.get("prefixes", []):
                if self.text.startswith(prefix):
                    return self.text[len(prefix):].strip()
            for suffix in spec.get("suffixes", []):
                if self.text.endswith(suffix):
                    return self.text[:-len(suffix)].strip()
            return None

        # Generic fallback
        for suffix in self.GENERIC_SUFFIXES:
            if self.text.endswith(suffix):
                return self.text[:-len(suffix)].strip()

        return None


# For backward compatibility
ByLanguage = YearPatternStripper


class TitlesTranslationsRenderer:
    """
    Builds a translations dict from `title_new`-shaped input by stripping
    the trailing/leading `{year}` pattern from both the English key and
    each language's translated text.
    """

    def __init__(self, title_new: dict[str, dict[str, str]]) -> None:
        self.title_new = title_new

    @staticmethod
    def _text_by_lang(lang: str, text: str) -> str | None:
        return YearPatternStripper(lang, text).run()

    def _render_translations(self, translations: dict[str, str]) -> dict[str, str]:
        new_key_data = {}
        for lang, str_text in translations.items():
            if not str_text:
                continue

            new_text = self._text_by_lang(lang, str_text)
            if new_text and new_text != str_text:
                new_key_data[lang] = new_text

        return new_key_data

    def run(self) -> dict[str, dict[str, str]]:
        data: dict[str, dict[str, str]] = {}

        for en_key, translations in self.title_new.items():
            new_key = self._text_by_lang("en", en_key)
            if new_key is None or new_key == en_key:
                continue

            new_key_data = self._render_translations(translations)
            if new_key_data:
                data[new_key] = new_key_data

        return data


class YearFreeTitleMerger:
    """
    Merges year-free title translations into the mapping's standard translations dictionary.
    """

    def __init__(self, mapping: TranslationMapping) -> None:
        self.mapping = mapping
        self.changes: bool | None = None

    def _add_from_titles(self, titles_new: dict[str, dict[str, str]], new_keys: list[str]) -> dict[str, dict[str, str]]:
        title_new_translations = TitlesTranslationsRenderer(titles_new).run()
        result = {x: v for x, v in title_new_translations.items() if x not in new_keys}
        return result

    def run(self) -> None:
        """Insert new translations into the translations dictionary."""
        titles_new = self.mapping.title_new
        new_translations = self.mapping.new

        if not titles_new:
            self.changes = False
            return

        new_keys = list(new_translations.keys())

        new_data = self._add_from_titles(titles_new, new_keys)
        if new_data:
            new_translations.update(new_data)
            self.changes = True
        else:
            self.changes = False


# For backward compatibility
AddTitlesTranslationsFromTitles = YearFreeTitleMerger


# ---------------------------------------------------------------------------
# Pure / Explicit APIs
# ---------------------------------------------------------------------------

def derive_year_free_entries(
    title_new: dict[str, dict[str, str]],
) -> dict[str, dict[str, str]]:
    """
    Derives year-free translation entries from title templates containing {year}.
    """
    return TitlesTranslationsRenderer(title_new).run()


def merge_year_free_into_new(mapping: TranslationMapping) -> bool:
    """
    Merges year-free title translations from mapping.title_new into mapping.new.
    Returns True if mapping.new was modified.
    """
    merger = YearFreeTitleMerger(mapping)
    merger.run()
    return bool(merger.changes)


__all__ = [
    "YearPatternStripper",
    "ByLanguage",
    "TitlesTranslationsRenderer",
    "YearFreeTitleMerger",
    "AddTitlesTranslationsFromTitles",
    "derive_year_free_entries",
    "merge_year_free_into_new",
]
