# injection/steps/validate.py
from __future__ import annotations

from ...exceptions import (
    SvgContainsTrefError,
    SvgCssHasIdsError,
    SvgCssTooComplexError,
    SvgTextContainsDollarError,
)
from .base import PreparationContext, PreparationStep

SVG_NS = "http://www.w3.org/2000/svg"


class ValidateStructure(PreparationStep):
    def execute(self, ctx: PreparationContext) -> None:
        if ctx.root is None:
            return

        # <tref> elements are not supported.
        trefs = ctx.root.findall(f".//{{{SVG_NS}}}tref")
        if len(trefs) != 0:
            raise SvgContainsTrefError(code="structure-error-contains-tref", element=trefs[0])

        # 2. Check CSS styling
        styles = ctx.root.findall(f".//{{{SVG_NS}}}style")
        for s in styles:
            css = s.text or ""
            if "#" in css:
                # CSS has IDs, too complex
                raise SvgCssHasIdsError(code="structure-error-css-has-ids", element=s)

            # Find complex selectors
            if "{" in css:
                selectors = [part.split("{")[0].strip() for part in css.split("}") if "{" in part]
                for sel in selectors:
                    if "," in sel or " " in sel or ">" in sel or ":" in sel:
                        raise SvgCssTooComplexError(code="structure-error-css-too-complex", element=s)

        # 3. Check for '$' placeholders in text content
        for text_el in ctx.root.findall(f".//{{{SVG_NS}}}text"):
            text_content = "".join(text_el.itertext())
            if "$" in text_content:
                raise SvgTextContainsDollarError(code="structure-error-text-contains-dollar", element=text_el)
