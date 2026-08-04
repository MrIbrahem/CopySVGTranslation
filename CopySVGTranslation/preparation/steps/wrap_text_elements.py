# split_languages_test.py
from __future__ import annotations

import re

from lxml import etree

from ...exceptions import SvgNonTspanInsideTextError, SvgStructureError
from ...utils import normalize_lang
from .base import PreparationContext, PreparationStep

SVG_NS = "http://www.w3.org/2000/svg"

class WrapTextElements(PreparationStep):
    def execute(self, ctx: PreparationContext) -> None:
        if ctx.root is None:
            return

        self._process_text_elements(ctx)

    # ------------------------------------------------------------------
    # Step 5: <text> structural checks and <switch> wrapping
    # ------------------------------------------------------------------
    def _process_text_elements(self, ctx: PreparationContext) -> None:
        """
        Second pass on <text> elements: reject '$N' placeholders, normalize
        systemLanguage, ensure each <text> is wrapped in a <switch>, move
        style up to the switch, and verify only <tspan> children are present.
        """
        if ctx.root is None:
            return

        texts = ctx.root.findall(f".//{{{SVG_NS}}}text")
        for text in texts:
            content = "".join(text.itertext())
            if re.search(r"\$[0-9]+", content):
                raise SvgStructureError(code="structure-error-text-contains-dollar")

            if self.config.normalize_languages:
                # normalize systemLanguage if present
                system_language = text.get("systemLanguage")
                if system_language:
                    normalized = normalize_lang(system_language)
                    if normalized != system_language:
                        text.set("systemLanguage", normalized)

            parent = text.getparent()
            if parent is None or (parent.tag not in ({f"{{{SVG_NS}}}switch", "switch"})):
                # Create a switch element in the SVG namespace and move the text into it
                switch = etree.Element(f"{{{SVG_NS}}}switch")
                parent_of_text = parent
                if parent_of_text is None:
                    raise SvgStructureError(code="structure-error-no-parent-for-text")

                # insert switch before text
                idx = list(parent_of_text).index(text)
                parent_of_text.insert(idx, switch)
                switch.append(text)

            # move style from text to switch (parent)
            if text.get("style"):
                switch_parent = text.getparent()
                if switch_parent is not None:
                    switch_parent.set("style", text.get("style"))

            # verify that children of text are only tspans or text nodes
            for child in text:
                if isinstance(child.tag, str) and child.tag not in ({f"{{{SVG_NS}}}tspan", "tspan"}):
                    raise SvgNonTspanInsideTextError(code="structure-error-non-tspan-inside-text", element=child)


__all__ = [
    "WrapTextElements",
]
