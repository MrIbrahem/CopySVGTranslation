# injection/steps/normalize_tspans.py
from __future__ import annotations

import re

from lxml import etree

from ...exceptions import SvgNestedTspanExceptionError
from ...injection import SvgStructureExceptionError
from .base import PreparationContext, PreparationStep

SVG_NS = "http://www.w3.org/2000/svg"


class NormalizeTspans(PreparationStep):
    def execute(self, ctx: PreparationContext) -> None:
        """Collect leaf <tspan> elements as translatable nodes; reject nested ones."""
        if ctx.root is None:
            return
        # Process tspans
        tspans = ctx.root.findall(".//{%s}tspan" % SVG_NS)
        for tspan in tspans:
            # nested content check: tspan should not have element children
            element_children = [c for c in tspan if isinstance(c.tag, str)]
            if len(element_children) == 0:
                ctx.translatable_nodes.append(tspan)
            else:
                # Nested tspans or children not supported
                # raise SvgStructureExceptionError('structure-error-nested-tspans-not-supported', tspan, element_children)
                node_text = etree.tostring(tspan, pretty_print=True).decode("utf-8")
                raise SvgNestedTspanExceptionError(tspan, [tspan.get("id", "")], node_text=node_text)

        # self._wrap_loose_text_into_tspans(ctx)


class WrapTspans(PreparationStep):
    # ------------------------------------------------------------------
    # Step 4: text/tspan normalization
    # ------------------------------------------------------------------
    def execute(self, ctx: PreparationContext) -> None:
        """Wrap raw text nodes (before first child, or as tails) into <tspan>."""
        texts = ctx.root.findall(".//{%s}text" % SVG_NS)
        for text in texts:
            # handle text before first child
            if (text.text or "").strip():
                tspan = etree.Element("{%s}tspan" % SVG_NS)
                tspan.text = text.text
                text.text = None
                text.insert(0, tspan)
                ctx.translatable_nodes.append(tspan)

            # handle tails after children
            children = list(text)
            for child in children:
                if (child.tail or "").strip():
                    new_tspan = etree.Element("{%s}tspan" % SVG_NS)
                    new_tspan.text = child.tail
                    child.tail = None
                    # insert after child
                    insert_index = list(text).index(child) + 1
                    text.insert(insert_index, new_tspan)
                    ctx.translatable_nodes.append(new_tspan)

            # accumulate the text element itself as translatable node
            ctx.translatable_nodes.append(text)

        self._clean_ids_and_remove_empty_nodes(ctx)
        self._rebuild_translatable_nodes(ctx)

    def _clean_ids_and_remove_empty_nodes(self, ctx: PreparationContext) -> None:
        """Normalize/validate ids on translatable nodes and drop empty nodes."""
        for node in list(ctx.translatable_nodes):
            node_id = node.get("id")
            if node_id is not None:
                original_id = node_id
                node_id = node_id.strip()
                if node_id != original_id:
                    ctx.existing_ids.discard(original_id)
                if not node_id:
                    node.attrib.pop("id", None)
                    node_id = None
                else:
                    node.set("id", node_id)
                    if "|" in node_id or "/" in node_id:
                        raise SvgStructureExceptionError("structure-error-invalid-node-id", node, [node_id])
                    m = re.match(r"^trsvg([0-9]+)$", node_id)
                    if m:
                        ctx.ids_in_use.append(int(m.group(1)))
                    if node_id.isdigit():
                        node.attrib.pop("id", None)
                        ctx.existing_ids.discard(node_id)
                        node_id = None
                    else:
                        ctx.existing_ids.add(node_id)
            # remove empty nodes with no children and no text
            if (not list(node)) and (not (node.text and node.text.strip())):
                node_id = node.get("id")
                if node_id:
                    ctx.existing_ids.discard(node_id)
                parent = node.getparent()
                if parent is not None:
                    parent.remove(node)
                # also remove from translatable_nodes list
                try:
                    ctx.translatable_nodes.remove(node)
                except ValueError:
                    pass

    def _rebuild_translatable_nodes(self, ctx: PreparationContext) -> None:
        """Rebuild translatable_nodes after removals (tspans then texts)."""
        ctx.translatable_nodes = []
        ctx.translatable_nodes.extend(ctx.root.findall(".//{%s}tspan" % SVG_NS))
        ctx.translatable_nodes.extend(ctx.root.findall(".//{%s}text" % SVG_NS))
