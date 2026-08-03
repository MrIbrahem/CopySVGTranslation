from __future__ import annotations

from pathlib import Path

from lxml import etree

from ..config import TranslationConfig
from .steps import (
    AssignIds,
    LoadDocument,
    NormalizeTspans,
    PreparationContext,
    PreparationStep,
    ReorderTexts,
    SplitLanguages,
    ValidateStructure,
)


class SvgPreparationPipeline:
    def __init__(self, config: TranslationConfig) -> None:
        self.config = config
        self.steps: list[PreparationStep] = [
            LoadDocument(config),
            ValidateStructure(config),
            NormalizeTspans(config),
            AssignIds(config),
            SplitLanguages(config),
            ReorderTexts(config),
        ]

    def run(self, path: Path) -> tuple[etree._ElementTree[etree._Element], etree._Element]:
        ctx = PreparationContext(path=path, config=self.config)
        for step in self.steps:
            step.execute(ctx)
        return ctx.tree, ctx.root
