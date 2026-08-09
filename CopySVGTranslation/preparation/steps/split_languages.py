# preparation/steps/split_languages.py
from __future__ import annotations

import copy
import re

from lxml import etree

from ...utils import split_lang_list
from .base import PreparationContext, PreparationStep
from .validate_switch import ValidateSwitchLanguages

SVG_NS = "http://www.w3.org/2000/svg"


def _clone_element(el: etree._Element) -> etree._Element:
    return copy.deepcopy(el)


class SplitLanguages(PreparationStep):
    """
    Expand comma-separated systemLanguage values into separate <text> nodes.
    """

    def execute(self, ctx: PreparationContext) -> None:
        self._split_switch_languages(ctx)

    def _split_switch_languages(self, ctx: PreparationContext) -> None:
        if ctx.root is None:
            return

        for switch in ctx.root.findall(f".//{{{SVG_NS}}}switch"):
            self._split_languages_in_switch(switch, ctx)

    def _split_languages_in_switch(
        self,
        switch: etree._Element,
        ctx: PreparationContext,
    ) -> None:
        # Run validation so unit tests and steps behave as expected
        validator = ValidateSwitchLanguages(self.config)
        validator._validate_switch(switch)

        for text_el in list(switch):
            if not isinstance(text_el.tag, str):
                continue
            if text_el.tag not in (f"{{{SVG_NS}}}text", "text"):
                continue

            sys_lang = text_el.get("systemLanguage")
            real_langs = split_lang_list(sys_lang) or ["fallback"]

            if len(real_langs) == 1:
                self._apply_single_lang(text_el, real_langs[0])
                continue

            # Keep first language on the original node
            self._apply_single_lang(text_el, real_langs[0])

            parent_list = list(switch)
            index = parent_list.index(text_el)

            for extra_lang in real_langs[1:]:
                cloned = _clone_element(text_el)
                self._apply_single_lang(cloned, extra_lang)
                self._reassign_ids(cloned, ctx)
                switch.insert(index + 1, cloned)
                index += 1

    @staticmethod
    def _apply_single_lang(text_el: etree._Element, lang: str) -> None:
        if lang == "fallback":
            text_el.attrib.pop("systemLanguage", None)
        else:
            text_el.set("systemLanguage", lang)

    def _reassign_ids(self, element: etree._Element, ctx: PreparationContext) -> None:
        if ctx.id_manager is None:
            return

        el_id = element.get("id")
        if el_id and re.match(r"^trsvg[0-9]+$", el_id):
            el_id = None

        if el_id:
            new_id = ctx.id_manager.allocate_clone(
                el_id, element.get("systemLanguage", "")
            )
        else:
            new_id = ctx.id_manager.allocate_trsvg()

        element.set("id", new_id)


__all__ = ["SplitLanguages"]
