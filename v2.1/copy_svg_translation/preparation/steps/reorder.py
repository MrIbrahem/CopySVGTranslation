# injection/steps/reorder.py
from __future__ import annotations

from ...utils import sort_switch_children
from .base import PreparationContext, PreparationStep

SVG_NS = "http://www.w3.org/2000/svg"


class ReorderTexts(PreparationStep):

    # ------------------------------------------------------------------
    # Step 7: final ordering
    # ------------------------------------------------------------------
    def execute(self, ctx: PreparationContext) -> None:
        """
        Simple deterministic reordering: for every <switch>, sort child <text>
        elements by the numeric part of their id if present, otherwise keep
        original order. 'fallback' (no systemLanguage) is placed last.
        """
        if ctx.root is None:
            return

        switches = ctx.root.findall(f".//{{{SVG_NS}}}switch")
        for switch in switches:
            sort_switch_children(switch, put_fallback_last=True)


__all__ = [
    "ReorderTexts",
]
