# injection/steps/split_languages.py
from __future__ import annotations

import copy
import re

from lxml import etree

from ...utils import split_lang_list
from .base import PreparationContext, PreparationStep

SVG_NS = "http://www.w3.org/2000/svg"


def _clone_element(el: etree._Element) -> etree._Element:
    """Deep-clone an element."""
    return copy.deepcopy(el)


class SplitLanguages(PreparationStep):
    def execute(self, ctx: PreparationContext) -> None:
        if ctx.root is None:
            return

        self._split_switch_languages(ctx)
        # ------------------------------------------------------------------
        # Step 6: <switch> language splitting
        # ------------------------------------------------------------------

    def _split_switch_languages(self, ctx: PreparationContext) -> None:
        """Split comma-separated systemLanguage values into cloned <text> nodes."""
        switches = ctx.root.findall(f".//{{{SVG_NS}}}switch")
        for switch in switches:
            self._split_languages_in_switch(switch, ctx)

    def _split_languages_in_switch(self, switch: etree._Element, ctx: PreparationContext) -> None:
        texts = switch.findall(f"./{{{SVG_NS}}}text")
        for text_el in texts:
            sys_lang = text_el.get("systemLanguage")

            if not sys_lang:
                continue

            real_langs = split_lang_list(sys_lang)
            if len(real_langs) <= 1:
                # 0 or 1 languages, standard systemLanguage
                if real_langs:
                    lang_value = real_langs[0]
                    if lang_value == "fallback":
                        text_el.attrib.pop("systemLanguage", None)
                    else:
                        text_el.set("systemLanguage", lang_value)
                continue

            # Split into multiple single-language <text> nodes
            parent_list = list(switch)
            index = parent_list.index(text_el)

            # Keep the first language in the original node
            original_lang = real_langs[0]
            if original_lang == "fallback":
                text_el.attrib.pop("systemLanguage", None)
            else:
                text_el.set("systemLanguage", original_lang)

            # For subsequent languages, clone the node and allocate new IDs
            for extra_lang in real_langs[1:]:
                cloned = _clone_element(text_el)
                if extra_lang == "fallback":
                    cloned.attrib.pop("systemLanguage", None)
                else:
                    cloned.set("systemLanguage", extra_lang)

                # Assign new unique IDs
                self._reassign_ids(cloned, ctx)

                switch.insert(index + 1, cloned)
                index += 1

    def _reassign_ids(self, element: etree._Element, ctx: PreparationContext) -> None:
        if ctx.id_manager is None:
            return

        el_id = element.get("id")

        if el_id and re.match(r"^trsvg[0-9]+$", el_id):
            el_id = None

        if el_id:
            new_id = ctx.id_manager.allocate_clone(el_id, element.get("systemLanguage", ""))
        else:
            new_id = ctx.id_manager.allocate_trsvg()

        element.set("id", new_id)

        # Children
        for child in element:
            self._reassign_ids(child, ctx)
