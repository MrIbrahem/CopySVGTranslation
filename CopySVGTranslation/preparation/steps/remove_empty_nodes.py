# preparation/steps/remove_empty_nodes.py
from __future__ import annotations

from .base import PreparationContext, PreparationStep

SVG_NS = "http://www.w3.org/2000/svg"


class RemoveEmptyNodes(PreparationStep):
    """
    Drop empty <text> and <tspan> nodes (no children and no text).
    Must run after ID assignment so we can unregister IDs cleanly.
    """

    def execute(self, ctx: PreparationContext) -> None:
        if ctx.root is None:
            return

        if ctx.id_manager is None:
            raise ValueError("id_manager is not set")

        candidates = (
            ctx.root.findall(f".//{{{SVG_NS}}}tspan")
            + ctx.root.findall(f".//{{{SVG_NS}}}text")
        )

        for node in list(candidates):
            if list(node) or node.text:
                continue

            node_id = node.get("id")
            if node_id:
                ctx.id_manager.existing_ids.discard(node_id)

            parent = node.getparent()
            if parent is not None:
                parent.remove(node)


__all__ = ["RemoveEmptyNodes"]
