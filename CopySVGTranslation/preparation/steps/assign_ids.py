# injection/steps/assign_ids.py
from __future__ import annotations

from .base import PreparationContext, PreparationStep

SVG_NS = "http://www.w3.org/2000/svg"


class AssignIds(PreparationStep):
    def execute(self, ctx: PreparationContext) -> None:
        if ctx.root is None:
            return

        for element in ctx.root.xpath("//*[@id]"):
            element_id = element.get("id")
            if not element_id:
                continue
            trimmed = element_id.strip()
            if trimmed != element_id:
                element.set("id", trimmed)
            ctx.existing_ids.add(trimmed)
