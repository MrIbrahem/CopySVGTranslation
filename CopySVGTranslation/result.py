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
    all_languages_count: int = 0
    new_languages_count: int = 0

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
            "all_languages_count": self.all_languages_count,
            "new_languages_count": self.new_languages_count,
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
    inject_stats: InjectorStats = field(default_factory=InjectorStats)

    def to_json(self) -> dict[str, Any]:
        inject_stats = self.inject_stats.to_json()
        return {
            "tree": self.tree,
            "inject_stats": inject_stats,
            "error": inject_stats["error"],
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


__all__ = [
    "InjectorStats",
    "InjectorData",
    "OperationResult",
]
