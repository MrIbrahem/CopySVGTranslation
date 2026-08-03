"""Helpers for injecting translations into SVG files."""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from typing import Any

from lxml import etree

logger = logging.getLogger(__name__)


@dataclass
class InjectorStats:
    """
    {
        "all_languages": 0,
        "new_languages": 0,
        "languages_before": [],
        "languages_after": [],
        "processed_switches": 0,
        "inserted_translations": 0,
        "skipped_translations": 0,
        "updated_translations": 0,
        "error": "",
    }"""

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
        return asdict(self)

    def _update(self, **kwargs):
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


__all__ = [
    "InjectorStats",
    "InjectorData",
]
