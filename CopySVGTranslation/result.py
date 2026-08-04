"""
TODO: write docs
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Generic, TypeVar

from lxml import etree

T = TypeVar("T")


@dataclass(slots=True)
class InjectorStats:
    all_languages: int = 0
    new_languages: int = 0

    processed_switches: int = 0
    inserted_translations: int = 0
    skipped_translations: int = 0
    updated_translations: int = 0

    languages_before: list[str] = field(default_factory=list)
    languages_after: list[str] = field(default_factory=list)
    error: str = ""

    def to_json(self) -> dict[str, Any]:
        """
        Serialize stats to a JSON-compatible dictionary.
        return {
            "all_languages": self.all_languages,
            "new_languages": self.new_languages,
            "processed_switches": self.processed_switches,
            "inserted_translations": self.inserted_translations,
            "skipped_translations": self.skipped_translations,
            "updated_translations": self.updated_translations,
            "languages_before": self.languages_before,
            "languages_after": self.languages_after,
            "error": self.error,
        }
        """
        return asdict(self)

    def _update(self, **kwargs) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)


@dataclass
class InjectorData:
    """Container for SVG data."""

    tree: etree._ElementTree | None = None
    new_stats: InjectorStats = field(default_factory=InjectorStats)

    def to_json(self) -> dict[str, Any]:
        new_stats = self.new_stats.to_json()
        return {
            "tree": self.tree,
            "new_stats": new_stats,
            "error": new_stats["error"],
        }


@dataclass(slots=True)
class OperationResult(Generic[T]):
    success: bool
    data: T | None = None
    stats: InjectorStats | None = None
    error: str | None = None
    error_code: str | None = None
    warnings: list[str] = field(default_factory=list)

    @classmethod
    def ok(
        cls,
        data: T,
        stats: InjectorStats | None = None,
        warnings: list[str] | None = None,
    ) -> OperationResult[T]:
        return cls(
            success=True,
            data=data,
            stats=stats,
            warnings=warnings or [],
        )

    @classmethod
    def fail(
        cls,
        error: str,
        error_code: str | None = None,
        stats: InjectorStats | None = None,
        warnings: list[str] | None = None,
    ) -> OperationResult[T]:
        return cls(
            success=False,
            error=error,
            error_code=error_code,
            stats=stats,
            warnings=warnings or [],
        )


# Convenience aliases
ExtractResult = OperationResult["TranslationMapping"]  # type: ignore # forward ref
InjectResult = OperationResult["InjectorData"]
