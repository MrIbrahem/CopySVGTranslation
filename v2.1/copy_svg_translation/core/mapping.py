# core/mapping.py
from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True, frozen=True)
class TranslationEntry:
    """One source string and its per-language translations."""

    source: str
    translations: Mapping[str, str] = field(default_factory=dict)

    def get(self, lang: str, default: str | None = None) -> str | None:
        return self.translations.get(lang, default)

    def languages(self) -> set[str]:
        return set(self.translations.keys())


@dataclass(slots=True)
class TranslationMapping:
    """
    Full mapping produced by extraction and consumed by injection.

    Attributes
    ----------
    new:
        Main map: normalized source text → {lang: translated text}
    title_new:
        Optional year-title variants advanced use
    tspans_by_id:
        Optional diagnostic map from extraction (id → default text)
    """

    new: dict[str, dict[str, str]] = field(default_factory=dict)
    title_new: dict[str, dict[str, str]] = field(default_factory=dict)
    tspans_by_id: dict[str, str] = field(default_factory=dict)
    meta: dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Factory helpers
    # ------------------------------------------------------------------
    @classmethod
    def from_any(cls, data: Mapping[str, Any] | TranslationMapping) -> TranslationMapping:
        if isinstance(data, TranslationMapping):
            return data
        return cls(
            new=dict(data.get("new", data if "new" not in data else {})),
            title_new=dict(data.get("title_new", {})),
            tspans_by_id=dict(data.get("tspans_by_id", {})),
            meta=dict(data.get("meta", {})),
        )

    @classmethod
    def from_extractor_data(cls, data: Mapping[str, Any]) -> TranslationMapping:
        """Create from the dict currently returned by the legacy extractor."""
        return cls.from_any(data)

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------
    def is_empty(self) -> bool:
        return not self.new and not self.title_new

    def all_languages(self) -> set[str]:
        langs: set[str] = set()
        for section in (self.new, self.title_new):
            for trans in section.values():
                langs.update(trans.keys())
        return langs

    def lookup(self, source: str, *, case_insensitive: bool = True) -> dict[str, str]:
        """Return {lang: text} for a source string, or empty dict."""
        key = source.lower() if case_insensitive else source
        if case_insensitive:
            for k, v in self.new.items():
                if k.lower() == key:
                    return dict(v)
            return {}
        return dict(self.new.get(key, {}))

    def entries(self) -> Iterator[TranslationEntry]:
        for source, trans in self.new.items():
            yield TranslationEntry(source=source, translations=trans)

    # ------------------------------------------------------------------
    # Mutation helpers (used while building the mapping)
    # ------------------------------------------------------------------
    def add(self, source: str, lang: str, text: str, *, case_insensitive: bool = True) -> None:
        key = source.lower() if case_insensitive else source
        self.new.setdefault(key, {})[lang] = text

    def merge(self, other: TranslationMapping | Mapping[str, Any]) -> None:
        other = self.from_any(other)
        for source, trans in other.new.items():
            self.new.setdefault(source, {}).update(trans)
        for source, trans in other.title_new.items():
            self.title_new.setdefault(source, {}).update(trans)
        self.tspans_by_id.update(other.tspans_by_id)

    def to_json(self) -> dict[str, Any]:
        return {
            "new": self.new,
            "title_new": self.title_new,
            "tspans_by_id": self.tspans_by_id,
            "meta": self.meta,
        }


__all__ = [
    "TranslationEntry",
    "TranslationMapping",
]
