# injection/steps/split_languages.py
from __future__ import annotations

import copy

from lxml import etree

from ...utils.text import split_lang_list
from .base import PreparationContext, PreparationStep

SVG_NS = "http://www.w3.org/2000/svg"


class SplitLanguages(PreparationStep):
    def execute(self, ctx: PreparationContext) -> None:
        if ctx.root is None:
            return

        switches = ctx.root.findall(f".//{{{SVG_NS}}}switch")
        for switch in switches:
            self._split_languages_in_switch(switch, ctx)

    def _split_languages_in_switch(self, switch: etree._Element, ctx: PreparationContext) -> None:
        texts = switch.findall(f"./{{{SVG_NS}}}text")
        for text_el in texts:
            sys_lang = text_el.get("systemLanguage")
            if not sys_lang:
                continue

            langs = split_lang_list(sys_lang)
            if len(langs) <= 1:
                # 0 or 1 languages, standard systemLanguage
                if langs:
                    text_el.set("systemLanguage", langs[0])
                continue

            # Split into multiple single-language <text> nodes
            parent_list = list(switch)
            index = parent_list.index(text_el)

            # Keep the first language in the original node
            text_el.set("systemLanguage", langs[0])

            # For subsequent languages, clone the node and allocate new IDs
            for extra_lang in langs[1:]:
                cloned = copy.deepcopy(text_el)
                cloned.set("systemLanguage", extra_lang)

                # Assign new unique IDs
                self._reassign_ids(cloned, ctx)

                switch.insert(index + 1, cloned)
                index += 1

    def _reassign_ids(self, element: etree._Element, ctx: PreparationContext) -> None:
        if ctx.id_manager is None:
            return

        el_id = element.get("id")
        if el_id:
            new_id = ctx.id_manager.allocate_clone(el_id, element.get("systemLanguage", ""))
            element.set("id", new_id)

        # Children
        for child in element:
            self._reassign_ids(child, ctx)
