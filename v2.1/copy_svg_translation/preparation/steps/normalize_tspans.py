# injection/steps/normalize_tspans.py
from __future__ import annotations

import re

from lxml import etree

from ...exceptions import SvgStructureError
from ...nested import NestedTspanFlattener
from .base import PreparationContext, PreparationStep

SVG_NS = "http://www.w3.org/2000/svg"


class NormalizeTspans(PreparationStep):
    def execute(self, ctx: PreparationContext) -> None:
        """Collect leaf <tspan> elements as translatable nodes; reject nested ones."""
        if ctx.root is None:
            return

        # 1. Process nested tspans using Flattener
        flattener = NestedTspanFlattener(self.config.nested_strategy)
        flattener.process(ctx.root)

        # 2. Wrap loose text directly under <text> into <tspan>
        for text_el in ctx.root.findall(f".//{{{SVG_NS}}}text"):
            self._wrap_loose_text(text_el)

        # 3. Rebuild the list of translatable nodes before _clean_ids_and_remove_empty_nodes
        self._rebuild_translatable_nodes(ctx)

    def _wrap_loose_text(self, text_el: etree._Element) -> None:
        # If there are no children, we wrap the entire text
        children = list(text_el)
        if not children:
            if text_el.text and text_el.text.strip():
                tspan = etree.Element(f"{{{SVG_NS}}}tspan")
                tspan.text = text_el.text
                text_el.text = None
                text_el.append(tspan)
            return

        # If there are already children but also text before first child, wrap it
        if text_el.text and text_el.text.strip():
            tspan = etree.Element(f"{{{SVG_NS}}}tspan")
            tspan.text = text_el.text
            text_el.text = None
            text_el.insert(0, tspan)

        # handle tails after children
        # Wrap text tails between elements
        for child in children:
            if child.tail and child.tail.strip():
                new_tspan = etree.Element(f"{{{SVG_NS}}}tspan")
                new_tspan.text = child.tail
                child.tail = None
                # insert after child
                idx = text_el.index(child)
                text_el.insert(idx + 1, new_tspan)

    def _rebuild_translatable_nodes(self, ctx: PreparationContext) -> None:
        """Rebuild translatable_nodes after removals (tspans then texts)."""
        if ctx.root is None:
            return

        ctx.translatable_nodes = ctx.root.findall(f".//{{{SVG_NS}}}tspan") + ctx.root.findall(f".//{{{SVG_NS}}}text")


class WrapTspans(PreparationStep):
    # ------------------------------------------------------------------
    # Step 4: text/tspan normalization
    # ------------------------------------------------------------------
    def execute(self, ctx: PreparationContext) -> None:
        """Wrap raw text nodes (before first child, or as tails) into <tspan>."""
        if ctx.root is None:
            return
        # self._clean_ids_and_remove_empty_nodes(ctx)

    def _clean_ids_and_remove_empty_nodes(self, ctx: PreparationContext) -> None:
        """Normalize/validate ids on translatable nodes and drop empty nodes."""
        if ctx.id_manager is None:
            raise ValueError("id_manager is not set")

        for node in list(ctx.translatable_nodes):
            node_id = node.get("id")
            if node_id is not None:
                original_id = node_id
                node_id = node_id.strip()
                if node_id != original_id:
                    ctx.id_manager.existing_ids.discard(original_id)
                if not node_id:
                    node.attrib.pop("id", None)
                    node_id = None
                else:
                    node.set("id", node_id)
                    if "|" in node_id or "/" in node_id:
                        raise SvgStructureError(code="structure-error-invalid-node-id")
                    m = re.match(r"^trsvg([0-9]+)$", node_id)
                    # if m:
                    # ctx.ids_in_use.append(int(m.group(1)))
                    if node_id.isdigit():
                        node.attrib.pop("id", None)
                        ctx.id_manager.existing_ids.discard(node_id)
                        node_id = None
                    else:
                        ctx.id_manager.register(node_id)

            # remove empty nodes with no children and no text
            # if (not list(node)) and (not (node.text and node.text.strip())):
            if (not list(node)) and (not node.text):
                node_id = node.get("id")
                if node_id:
                    ctx.id_manager.existing_ids.discard(node_id)
                parent = node.getparent()
                if parent is not None:
                    parent.remove(node)
                # also remove from translatable_nodes list
                try:
                    ctx.translatable_nodes.remove(node)
                except ValueError:
                    pass


__all__ = [
    "NormalizeTspans",
    "WrapTspans",
]
