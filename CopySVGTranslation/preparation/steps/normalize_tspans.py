# injection/steps/normalize_tspans.py
from __future__ import annotations

from lxml import etree

from ...exceptions import SvgNestedTspanExceptionError
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
