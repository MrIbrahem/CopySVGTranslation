# preparation/steps/validate_switch.py
from __future__ import annotations

from lxml import etree

from ...exceptions import SvgStructureError
from ...utils import split_lang_list
from .base import PreparationContext, PreparationStep

SVG_NS = "http://www.w3.org/2000/svg"


class ValidateSwitchLanguages(PreparationStep):
    """
    Early structural + language validation for every <switch>.

    Responsibilities (read-only):
    - Reject non-<text> children
    - Reject non-whitespace text content outside <text>
    - Reject duplicate languages inside one <text>
    - Reject the same language declared by two different <text> nodes
      (including the implicit "fallback")
    """

    def execute(self, ctx: PreparationContext) -> None:
        if ctx.root is None:
            return

        for switch in ctx.root.findall(f".//{{{SVG_NS}}}switch"):
            self._validate_switch(switch)

    def _validate_switch(self, switch: etree._Element) -> None:
        existing_langs: set[str] = set()

        for child in list(switch):
            # Non-element nodes (comments, etc.)
            if not isinstance(child.tag, str):
                if child.text and child.text.strip():
                    raise SvgStructureError(
                        code="structure-error-switch-text-content-outside-text",
                        element=switch,
                    )
                continue

            if child.tag not in (f"{{{SVG_NS}}}text", "text"):
                raise SvgStructureError(
                    code="structure-error-switch-child-not-text",
                    element=child,
                )

            sys_lang = child.get("systemLanguage")
            real_langs = split_lang_list(sys_lang) or ["fallback"]

            seen_in_this_text: set[str] = set()
            for lang in real_langs:
                if lang in seen_in_this_text:
                    raise SvgStructureError(
                        code="structure-error-multiple-lang-in-text",
                        extra=[lang],
                        element=child,
                    )
                seen_in_this_text.add(lang)

                if lang in existing_langs:
                    raise SvgStructureError(
                        code="structure-error-multiple-text-same-lang",
                        extra=[lang],
                        element=child,
                    )

            existing_langs.update(seen_in_this_text)


__all__ = ["ValidateSwitchLanguages"]
