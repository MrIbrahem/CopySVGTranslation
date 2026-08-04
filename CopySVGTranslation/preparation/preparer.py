"""Utilities to prepare SVG files for the injection phase."""

from __future__ import annotations

import logging
from pathlib import Path

from lxml import etree

from ..config import TranslationConfig
from ..injection.id_manager import IdManager
from .steps import (
    AssignIds,
    LoadDocument,
    NormalizeTspans,
    PreparationContext,
    PreparationStep,
    ReorderTexts,
    SplitLanguages,
    ValidateStructure,
    WrapTextElements,
    WrapTspans,
)

logger = logging.getLogger(__name__)


class SvgPreparationPipeline:
    """
    Prepares an SVG file for the translation phase.

    Ensures structural invariants are met before translations are injected:
    - every <text> lives inside a <switch>
    - every piece of translatable text is wrapped in a <tspan>
    - every translatable node has a unique, normalized id
    - systemLanguage attributes are normalized and split (comma-separated
      values are expanded into cloned <text> nodes)
    - <text> elements inside each <switch> are deterministically ordered
    """

    def __init__(self, config: TranslationConfig) -> None:
        self.config = config
        self.steps: list[PreparationStep] = [
            LoadDocument(config),
            ValidateStructure(config),
            NormalizeTspans(config),
            AssignIds(config),
            WrapTspans(config),
            WrapTextElements(config),
            SplitLanguages(config),
            ReorderTexts(config),
        ]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(self, source_file: Path) -> tuple[etree._ElementTree[etree._Element], etree._Element]:
        """Run all preparation steps and return the resulting tree and root."""
        # Reset per-run state to ensure idempotent behavior
        path = Path(str(source_file))

        self.ctx = PreparationContext(
            path=path,
            config=self.config,
            id_manager=IdManager(),
        )
        for step in self.steps:
            step.execute(self.ctx)

        return self.ctx.tree, self.ctx.root


def make_translation_ready(source_file: Path | str) -> tuple[etree._ElementTree, etree._Element]:
    """
    Legacy function-style wrapper around SvgPreparationPipeline, kept for
    backward compatibility with existing callers.
    """
    config = TranslationConfig()
    return SvgPreparationPipeline(config).run(source_file)


__all__ = [
    "SvgPreparationPipeline",
    "make_translation_ready",
]
