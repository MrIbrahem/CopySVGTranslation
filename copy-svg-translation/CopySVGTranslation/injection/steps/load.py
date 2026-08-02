# injection/steps/load.py
from __future__ import annotations

from ...io.svg_document import SvgDocument
from .base import PreparationContext, PreparationStep


class LoadDocument(PreparationStep):
    def execute(self, ctx: PreparationContext) -> None:
        doc = SvgDocument.load(ctx.path, config=ctx.config)
        ctx.tree = doc.tree
        ctx.root = doc.root
