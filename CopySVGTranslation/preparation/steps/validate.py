# injection/steps/validate.py
from __future__ import annotations

import re

from ...exceptions import (
    SvgContainsTrefError,
    SvgCssHasIdsError,
    SvgCssTooComplexError,
    SvgTextContainsDollarError,
    SvgNonTspanInsideTextError,
    SvgStructureError,
)
from ...utils import split_lang_list
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

        # Check for any <text> elements
        texts = ctx.root.findall(f".//{{{SVG_NS}}}text")
        if len(texts) == 0:
            return

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

        # 4. Check for switch child rules & duplicate languages
        switches = ctx.root.findall(f".//{{{SVG_NS}}}switch")
        for switch in switches:
            if switch.text and switch.text.strip():
                raise SvgStructureError(code="structure-error-switch-text-content-outside-text", element=switch)

            existing_langs = set()
            for child in list(switch):
                if child.tail and child.tail.strip():
                    raise SvgStructureError(code="structure-error-switch-text-content-outside-text", element=child)

                if not isinstance(child.tag, str):
                    # comments / other non-elements: if they have non-whitespace text, raise
                    if child.text and child.text.strip():
                        raise SvgStructureError(code="structure-error-switch-text-content-outside-text", element=child)
                    continue
                # All child elements of switch must be text elements
                if child.tag not in ({f"{{{SVG_NS}}}text", "text"}):
                    raise SvgStructureError(code="structure-error-switch-child-not-text", element=child)

                # Check for duplicate languages inside the switch
                sys_lang = child.get("systemLanguage")
                real_langs = split_lang_list(sys_lang) if sys_lang else ["fallback"]
                languages_present = set()
                for extra_lang in real_langs:
                    if extra_lang in languages_present:
                        raise SvgStructureError(code="structure-error-multiple-lang-in-text", element=child, extra=[extra_lang])
                    languages_present.add(extra_lang)
                    if extra_lang in existing_langs:
                        raise SvgStructureError(code="structure-error-multiple-text-same-lang", element=child, extra=[extra_lang])
                existing_langs.update(languages_present)

        # 5. Check only tspans inside <text>
        for text in ctx.root.findall(f".//{{{SVG_NS}}}text"):
            for child in text:
                if isinstance(child.tag, str) and child.tag not in ({f"{{{SVG_NS}}}tspan", "tspan"}):
                    raise SvgNonTspanInsideTextError(code="structure-error-non-tspan-inside-text", element=child)
