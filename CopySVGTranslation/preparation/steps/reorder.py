# injection/steps/reorder.py
from __future__ import annotations
import re

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

        # switches = ctx.root.findall(f".//{{{SVG_NS}}}switch")
        # for switch in switches:
        #     sort_switch_children(switch, put_fallback_last=True)

        switches = ctx.root.findall(".//{%s}switch" % SVG_NS)
        for sw in switches:
            texts = [c for c in sw if isinstance(c.tag, str) and c.tag in ({f"{{{SVG_NS}}}text", "text"})]

            def sort_key(el):
                lang = el.get("systemLanguage") or "fallback"
                m = re.search(r"trsvg(\d+)", (el.get("id") or ""))
                num = int(m.group(1)) if m else 10**9
                return (0 if lang == "fallback" else 1, num, lang)

            texts_sorted = sorted(texts, key=sort_key)
            # re-append in sorted order, leaving non-text children (if any) as-is
            for t in texts_sorted:
                sw.remove(t)
            for t in texts_sorted:
                sw.append(t)

