# injection/steps/reorder.py
from __future__ import annotations

from ...utils import sort_switch_children
from .base import PreparationContext, PreparationStep

SVG_NS = "http://www.w3.org/2000/svg"


class ReorderTexts(PreparationStep):
    def execute(self, ctx: PreparationContext) -> None:
        if ctx.root is None:
            return

        switches = ctx.root.findall(f".//{{{SVG_NS}}}switch")
        for switch in switches:
            sort_switch_children(switch, put_fallback_last=True)
