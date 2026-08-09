# preparation/steps/assign_ids.py
from __future__ import annotations

from ...exceptions import SvgInvalidIdError, SvgStructureError
from ...utils import collect_ids
from .base import PreparationContext, PreparationStep

SVG_NS = "http://www.w3.org/2000/svg"


class AssignIds(PreparationStep):
    """
    - Register all existing IDs.
    - Normalize / validate existing IDs on translatable nodes.
    - Allocate missing trsvgN IDs when config.assign_missing_ids is True.
    """

    def execute(self, ctx: PreparationContext) -> None:
        if ctx.root is None:
            return

        if ctx.id_manager is None:
            raise Exception("ID manager is not initialized")

        # Clean existing IDs on translatable nodes first so invalid ones are dropped/popped cleanly
        self._clean_existing_ids(ctx)

        # Register remaining valid IDs
        existing = collect_ids(ctx.root)
        ctx.id_manager.register_many(existing)

        # Reject completely empty id attributes on any remaining element
        for element in ctx.root.xpath("//*[@id]"):
            el_id = element.get("id")
            if not el_id or not el_id.strip():
                raise SvgInvalidIdError(
                    code="structure-error-invalid-node-id",
                    element=element,
                )

        if self.config.assign_missing_ids:
            self._assign_missing(ctx)

    def _clean_existing_ids(self, ctx: PreparationContext) -> None:
        assert ctx.id_manager is not None and ctx.root is not None

        nodes = (
            ctx.root.findall(f".//{{{SVG_NS}}}tspan")
            + ctx.root.findall(f".//{{{SVG_NS}}}text")
        )

        for node in nodes:
            node_id = node.get("id")
            if node_id is None:
                continue

            original = node_id
            node_id = node_id.strip()

            if node_id != original:
                ctx.id_manager.existing_ids.discard(original)

            if not node_id:
                node.attrib.pop("id", None)
                continue

            if "|" in node_id or "/" in node_id:
                raise SvgStructureError(code="structure-error-invalid-node-id")

            # Pure numeric IDs are not useful – drop them
            if node_id.isdigit():
                node.attrib.pop("id", None)
                ctx.id_manager.existing_ids.discard(node_id)
                continue

            node.set("id", node_id)
            ctx.id_manager.register(node_id)

    def _assign_missing(self, ctx: PreparationContext) -> None:
        assert ctx.id_manager is not None and ctx.root is not None

        for text_el in ctx.root.findall(f".//{{{SVG_NS}}}text"):
            if not text_el.get("id"):
                text_el.set("id", ctx.id_manager.allocate_trsvg())

            for tspan in text_el.findall(f"./{{{SVG_NS}}}tspan"):
                if not tspan.get("id"):
                    tspan.set("id", ctx.id_manager.allocate_trsvg())


__all__ = ["AssignIds"]
