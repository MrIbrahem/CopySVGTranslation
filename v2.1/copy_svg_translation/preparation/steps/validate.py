# injection/steps/validate.py
from __future__ import annotations

import re

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
            raise SvgContainsTrefError(element=trefs[0])

        # 2. Check CSS styling
        styles = ctx.root.findall(f".//{{{SVG_NS}}}style")
        css_simple_re = re.compile(r"^([^{]+\{[^}]*\})*[^{]+$")

        for s in styles:
            css = s.text or ""
            if "#" in css:
                # CSS has IDs, too complex
                if not css_simple_re.match(css):
                    raise SvgCssTooComplexError(extra=[s.get("id", "")])

                # split selectors roughly and ensure no '#' in selectors portion
                selectors = re.split(r"\{[^}]*\}", css)
                for selector in selectors:
                    if "#" in selector:
                        raise SvgCssHasIdsError(extra=[s.get("id", "")])

            # Find complex selectors
            if "{" in css:
                selectors = [part.split("{")[0].strip() for part in css.split("}") if "{" in part]
                for sel in selectors:
                    if "," in sel or " " in sel or ">" in sel or ":" in sel:
                        raise SvgCssTooComplexError(element=s)

        # 3. Check for '$' placeholders in text content
        for text_el in ctx.root.findall(f".//{{{SVG_NS}}}text"):
            text_content = "".join(text_el.itertext())
            if "$" in text_content:
                raise SvgTextContainsDollarError(code="structure-error-text-contains-dollar", element=text_el)
