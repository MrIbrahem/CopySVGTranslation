# injection/steps/validate.py
from __future__ import annotations

import re

from ...exceptions import SvgStructureError
from .base import PreparationContext, PreparationStep

SVG_NS = "http://www.w3.org/2000/svg"


class ValidateStructure(PreparationStep):
    def execute(self, ctx: PreparationContext) -> None:
        if ctx.root is None:
            return

        # <tref> elements are not supported.
        trefs = ctx.root.findall(f".//{{{SVG_NS}}}tref")
        if len(trefs) != 0:
            raise SvgStructureError(code="structure-error-contains-tref")

        # Check for any <text> elements
        texts = ctx.root.findall(f".//{{{SVG_NS}}}text")
        if len(texts) == 0:
            return

        styles = ctx.root.findall(f".//{{{SVG_NS}}}style")
        css_simple_re = re.compile(r"^([^{]+\{[^}]*\})*[^{]+$")

        for s in styles:
            css = s.text or ""
            if "#" in css:
                if not css_simple_re.match(css):
                    raise SvgStructureError(code="structure-error-css-too-complex", extra=[s.get("id", "")])

                # split selectors roughly and ensure no '#' in selectors portion
                selectors = re.split(r"\{[^}]*\}", css)
                for selector in selectors:
                    if "#" in selector:
                        raise SvgStructureError(code="structure-error-css-has-ids", extra=[s.get("id", "")])
