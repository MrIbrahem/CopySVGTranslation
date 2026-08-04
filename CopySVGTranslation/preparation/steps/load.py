# injection/steps/load.py
from __future__ import annotations

from ...io import SvgDocument
from .base import PreparationContext, PreparationStep


class LoadDocument(PreparationStep):
    def execute(self, ctx: PreparationContext) -> None:
        """Parse the SVG file and ensure it has a sane default namespace."""
        doc = SvgDocument.load(ctx.path, config=ctx.config)
        ctx.tree = doc.tree
        ctx.root = doc.root


__all__ = [
    "LoadDocument",
]
