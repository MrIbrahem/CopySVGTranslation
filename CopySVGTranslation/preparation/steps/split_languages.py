# injection/steps/split_languages.py
from __future__ import annotations

import copy
import re

from lxml import etree

from ...exceptions import SvgStructureError
from ...utils import normalize_lang, split_lang_list
from .base import PreparationContext, PreparationStep

SVG_NS = "http://www.w3.org/2000/svg"


def get_text_content(el: etree._Element) -> str:
    """Return concatenated text content of element (like DOM textContent)."""
    return "".join(el.itertext())


def _clone_element(el: etree._Element) -> etree._Element:
    """Deep-clone an element."""
    return copy.deepcopy(el)


class SplitLanguages(PreparationStep):
    def execute(self, ctx: PreparationContext) -> None:
        if ctx.root is None:
            return

        self._process_text_elements(ctx)
        self._split_switch_languages(ctx)

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
            content = get_text_content(text)
            if re.search(r"\$[0-9]+", content):
                raise SvgStructureError("structure-error-text-contains-dollar")

            # normalize systemLanguage if present
            if text.get("systemLanguage"):
                text.set("systemLanguage", normalize_lang(text.get("systemLanguage")))

            parent = text.getparent()
            if parent is None or (parent.tag not in ({f"{{{SVG_NS}}}switch", "switch"})):
                # Create a switch element in the SVG namespace and move the text into it
                switch = etree.Element(f"{{{SVG_NS}}}switch")
                parent_of_text = parent
                if parent_of_text is None:
                    raise SvgStructureError("structure-error-no-parent-for-text")
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
                if child.tag not in ({f"{{{SVG_NS}}}tspan", "tspan"}):
                    raise SvgStructureError("structure-error-non-tspan-inside-text")

    # ------------------------------------------------------------------
    # Step 6: <switch> language splitting
    # ------------------------------------------------------------------
    def _split_switch_languages(self, ctx: PreparationContext) -> None:
        """Split comma-separated systemLanguage values into cloned <text> nodes."""
        switches = ctx.root.findall(f".//{{{SVG_NS}}}switch")
        for switch in switches:
            self._split_languages_in_switch(switch, ctx)

    def _split_languages_in_switch(self, switch: etree._Element, ctx: PreparationContext) -> None:
        # gather existing languages for duplicate detection
        existing_langs: set[str] = set()
        # collect children first to avoid modifying while iterating

        children = list(switch)
        for text_el in children:
            if not self._validate_text_el_children(text_el):
                continue

            sys_lang = text_el.get("systemLanguage")
            real_langs = split_lang_list(sys_lang) if sys_lang else ["fallback"]

            languages_present: set[str] = set()
            for extra_lang in real_langs:
                if extra_lang in languages_present:
                    raise SvgStructureError("structure-error-multiple-lang-in-text", extra=[extra_lang])

                languages_present.add(extra_lang)
                if extra_lang in existing_langs:
                    raise SvgStructureError("structure-error-multiple-text-same-lang", extra=[extra_lang])

            if len(real_langs) == 1:
                lang_value = real_langs[0]
                if lang_value == "fallback":
                    if sys_lang:
                        text_el.attrib.pop("systemLanguage", None)
                else:
                    text_el.set("systemLanguage", lang_value)
                existing_langs.add(lang_value)
                continue

            # Split into multiple single-language <text> nodes
            parent_list = list(switch)
            index = parent_list.index(text_el)

            original_lang = real_langs[0]
            if original_lang == "fallback":
                text_el.attrib.pop("systemLanguage", None)
            else:
                text_el.set("systemLanguage", original_lang)
            existing_langs.add(original_lang)

            # For subsequent languages, clone the node and allocate new IDs
            for extra_lang in real_langs[1:]:
                if extra_lang in existing_langs:
                    raise SvgStructureError("structure-error-multiple-text-same-lang", extra=[extra_lang])
                cloned = _clone_element(text_el)
                if extra_lang == "fallback":
                    cloned.attrib.pop("systemLanguage", None)
                else:
                    cloned.set("systemLanguage", extra_lang)

                # Assign new unique IDs
                self._reassign_ids(cloned, ctx)

                existing_langs.add(extra_lang)
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

    def _validate_text_el_children(self, text_el) -> None:
        if not isinstance(text_el.tag, str):
            # ignore comments etc, but if there's text content outside elements, check whitespace
            if text_el.text and text_el.text.strip():
                raise SvgStructureError("structure-error-switch-text-content-outside-text")
            return False
        if text_el.tag not in ({f"{{{SVG_NS}}}text", "text"}):
            raise SvgStructureError("structure-error-switch-child-not-text")
        return True
