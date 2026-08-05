# injection/steps/base.py
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree

from ...config import TranslationConfig
from ...injection.id_manager import IdManager


@dataclass
class PreparationContext:
    path: Path
    config: TranslationConfig
    tree: etree._ElementTree | None = None
    root: etree._Element | None = None
    id_manager: IdManager | None = None
    translatable_nodes: list[etree._Element] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class PreparationStep(ABC):
    def __init__(self, config: TranslationConfig) -> None:
        self.config = config or TranslationConfig()

    @abstractmethod
    def execute(self, ctx: PreparationContext) -> None:
        """Modify ctx in-place. Raise on fatal errors."""
        ...


__all__ = [
    "PreparationContext",
    "PreparationStep",
]
