# injection/steps/assign_ids.py
from __future__ import annotations

from .base import PreparationContext, PreparationStep

SVG_NS = "http://www.w3.org/2000/svg"


class AssignIds(PreparationStep):
    def execute(self, ctx: PreparationContext) -> None:
        if ctx.root is None:
            return

        counter = max(ctx.ids_in_use) if ctx.ids_in_use else 0

        # Check all existing IDs for validity
        for element in ctx.root.xpath("//*[@id]"):
            el_id = element.get("id")
            if not el_id:
                continue
            trimmed = el_id.strip()
            if trimmed != el_id:
                element.set("id", trimmed)
            ctx.existing_ids.add(trimmed)

        # Automatically assign missing trsvgN IDs to <text> and <tspan> elements

        for text_el in ctx.root.findall(f".//{{{SVG_NS}}}text"):
            # Check text element itself
            if not text_el.get("id"):
                while f"trsvg{counter}" in ctx.existing_ids:
                    counter += 1
                new_id = f"trsvg{counter}"
                text_el.set("id", new_id)
                ctx.ids_in_use.append(counter)
                ctx.existing_ids.add(new_id)

            # Check children tspans
            for tspan in text_el.findall(f"./{{{SVG_NS}}}tspan"):
                if not tspan.get("id"):
                    while f"trsvg{counter}" in ctx.existing_ids:
                        counter += 1
                    new_id = f"trsvg{counter}"
                    tspan.set("id", new_id)
                    ctx.ids_in_use.append(counter)
                    ctx.existing_ids.add(new_id)
