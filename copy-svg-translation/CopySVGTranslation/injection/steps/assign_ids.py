# injection/steps/assign_ids.py
from __future__ import annotations

from lxml import etree

from ...exceptions import SvgInvalidIdError
from ...utils.xml import collect_ids
from .base import PreparationContext, PreparationStep

SVG_NS = "http://www.w3.org/2000/svg"


class AssignIds(PreparationStep):
    def execute(self, ctx: PreparationContext) -> None:
        if ctx.root is None:
            return

        # Initialize ID manager if not done
        existing_ids = collect_ids(ctx.root)
        if ctx.id_manager is None:
            from ..id_manager import IdManager

            ctx.id_manager = IdManager(existing_ids)
        else:
            ctx.id_manager.register_many(existing_ids)

        counter = 1

        # Check all existing IDs for validity
        for element in ctx.root.xpath("//*[@id]"):
            el_id = element.get("id")
            if not el_id or not el_id.strip():
                raise SvgInvalidIdError("structure-error-invalid-node-id", element=element)

        # Automatically assign missing trsvgN IDs to <text> and <tspan> elements
        if self.config.assign_missing_ids:
            for text_el in ctx.root.findall(f".//{{{SVG_NS}}}text"):
                # Check text element itself
                if not text_el.get("id"):
                    while f"trsvg{counter}" in ctx.id_manager.existing_ids:
                        counter += 1
                    new_id = f"trsvg{counter}"
                    text_el.set("id", new_id)
                    ctx.id_manager.register(new_id)

                # Check children tspans
                for tspan in text_el.findall(f"./{{{SVG_NS}}}tspan"):
                    if not tspan.get("id"):
                        while f"trsvg{counter}" in ctx.id_manager.existing_ids:
                            counter += 1
                        new_id = f"trsvg{counter}"
                        tspan.set("id", new_id)
                        ctx.id_manager.register(new_id)
