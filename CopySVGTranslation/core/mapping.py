# core/mapping.py
from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import asdict, dataclass, field
from typing import Any

from lxml import etree


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
    error: str | None = None

    # ------------------------------------------------------------------
    # Factory helpers
    # ------------------------------------------------------------------
    @classmethod
    def from_any(cls, data: Mapping[str, Any] | TranslationMapping) -> TranslationMapping:
        if isinstance(data, TranslationMapping):
            return data

        data_json = data

        if not isinstance(data_json, dict) and not isinstance(data_json, Mapping):
            raise TypeError(f"Expected Mapping/TranslationMapping/dict, got {type(data_json)}")

        return cls(
            new=dict(data_json.get("new", {})),
            title_new=dict(data_json.get("title_new", {})),
            tspans_by_id=dict(data_json.get("tspans_by_id", {})),
            meta=dict(data_json.get("meta", {})),
            error=data_json.get("error", ""),
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
            for translate in section.values():
                if isinstance(translate, dict):
                    langs.update(translate.keys())
                else:
                    raise TypeError(f"Unexpected type: {type(translate)}: section: {str(section)}")

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

    def merge(self, other: TranslationMapping | Mapping[str, Any], merge_keys: list[str] | None = None) -> None:
        """
        Mapping structure to understand merge logic:
        {
            "new": { "text, 1990": { "abr": "text, afe 1990", "ar": "نص، 1990" } },
            "tspans_by_id": { "trsvg1": "text, 1990" },
            "title_new": { "text, {year}": { "abr": "text, afe {year}", "ar": "نص، {year}" } },
            "meta": {
                "header": { "text, 1990": { "abr": "text, afe 1990", "ar": "نص، 1990" } }
            },
            "error": ""
        }
        """

        def _merge_dict(self_new, other_new) -> None:
            for source, lang_dict in other_new.items():
                self_new.setdefault(source, {})
                for lang, text in lang_dict.items():
                    if lang not in self_new[source]:
                        self_new[source][lang] = text

        if merge_keys is None:
            merge_keys = ["new", "title_new", "tspans_by_id"]

        other = self.from_any(other)

        # Merge new mapping
        # new structure: {"new": { "text, 1990": { "abr": "text, afe 1990", "ar": "نص، 1990" } }, ...}
        if "new" in merge_keys:
            _merge_dict(self.new, other.new)

        # Merge title_new mapping
        # title_new structure: {"title_new": { "text, {year}": { "abr": "text, afe {year}", "ar": "نص، {year}" } }, ...}
        if "title_new" in merge_keys:
            _merge_dict(self.title_new, other.title_new)

        # Merge tspans_by_id mapping
        if "tspans_by_id" in merge_keys:
            self.tspans_by_id.update(other.tspans_by_id)

        # Should we Merge meta?

    def to_json(self) -> dict[str, Any]:
        error = self.error or self.meta.get("error") or ""
        return {
            "new": self.new,
            "title_new": self.title_new,
            "tspans_by_id": self.tspans_by_id,
            "meta": self.meta,
            "error": error,
        }


@dataclass(slots=True)
class InjectorStats:
    all_languages_count: int = 0
    new_languages_count: int = 0

    processed_switches: int = 0
    inserted_translations: int = 0
    skipped_translations: int = 0
    updated_translations: int = 0

    languages_before: list[str] = field(default_factory=list)
    languages_after: list[str] = field(default_factory=list)

    def to_json(self) -> dict[str, Any]:
        """
        Serialize stats to a JSON-compatible dictionary.
        }
        """
        return asdict(self)

    def _update(self, **kwargs) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)

    def has_changes(self) -> bool:
        return any(
            (
                self.new_languages_count,
                self.updated_translations,
                self.inserted_translations,
            )
        )


@dataclass
class Error:
    code: str | None = None
    label: str | None = None

    def to_json(self) -> dict[str, Any]:
        return asdict(self)  # pyright: ignore[reportCallIssue]

    def from_error(self, exc: Exception | Any) -> None:
        label = getattr(exc, "label", None) or getattr(exc, "info", None)
        if label:
            self.label = str(label)

        code = getattr(exc, "code", None) or str(exc)
        if code:
            self.code = str(code)


@dataclass
class InjectorData:
    """Container for SVG data."""

    tree: etree._ElementTree | None = None
    inject_stats: InjectorStats = field(default_factory=InjectorStats)
    error: Error = field(default_factory=Error)

    def to_json(self) -> dict[str, Any]:
        inject_stats = self.inject_stats.to_json()

        return {
            "tree": self.tree,
            "inject_stats": inject_stats,
            "error": self.error.to_json() if (self.error.code or self.error.label) else None,
        }

    @classmethod
    def from_error(cls, exc) -> InjectorData:
        label = getattr(exc, "label", None) or getattr(exc, "info", None)
        error = Error(
            code=getattr(exc, "code", None) or str(exc),
            label=label,
        )
        return cls(error=error)


__all__ = [
    "TranslationEntry",
    "TranslationMapping",
]
