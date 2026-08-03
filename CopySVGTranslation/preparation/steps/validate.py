# injection/steps/validate.py
from __future__ import annotations
import re

from ...exceptions import SvgStructureExceptionError
from .base import PreparationContext, PreparationStep

SVG_NS = "http://www.w3.org/2000/svg"


class ValidateStructure(PreparationStep):
    def execute(self, ctx: PreparationContext) -> None:
        if ctx.root is None:
            return

        # Check for any <text> elements
        texts = ctx.root.findall(".//{%s}text" % SVG_NS)
        if len(texts) == 0:
            return

        styles = ctx.root.findall(".//{%s}style" % SVG_NS)
        css_simple_re = re.compile(r"^([^{]+\{[^}]*\})*[^{]+$")

        for s in styles:
            css = s.text or ""
            if "#" in css:
                if not css_simple_re.match(css):
                    raise SvgStructureExceptionError("structure-error-css-too-complex", None, [s.get("id", "")])
                # split selectors roughly and ensure no '#' in selectors portion
                selectors = re.split(r"\{[^}]*\}", css)
                for selector in selectors:
                    if "#" in selector:
                        raise SvgStructureExceptionError("structure-error-css-has-ids", None, [s.get("id", "")])
