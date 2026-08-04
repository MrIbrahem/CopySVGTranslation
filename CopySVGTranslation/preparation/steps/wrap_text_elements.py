# split_languages_test.py
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


class WrapTextElements(PreparationStep):
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
                raise SvgStructureError(code="structure-error-text-contains-dollar")

            if self.config.normalize_languages:
                # normalize systemLanguage if present
                system_language = text.get("systemLanguage")
                if system_language:
                    normalized = normalize_lang(system_language)
                    if normalized != system_language:
                        text.set("systemLanguage", normalized)

            parent = text.getparent()
            if parent is None or (parent.tag not in ({f"{{{SVG_NS}}}switch", "switch"})):
                # Create a switch element in the SVG namespace and move the text into it
                switch = etree.Element(f"{{{SVG_NS}}}switch")
                parent_of_text = parent
                if parent_of_text is None:
                    raise SvgStructureError(code="structure-error-no-parent-for-text")

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
                    raise SvgStructureError(code="structure-error-non-tspan-inside-text")

    # ------------------------------------------------------------------
    # Step 6: <switch> language splitting
    # ------------------------------------------------------------------

    def _split_switch_languages(self, ctx: PreparationContext) -> None:
        """Split comma-separated systemLanguage values into cloned <text> nodes."""
        if ctx.root is None:
            return

        switches = ctx.root.findall(f".//{{{SVG_NS}}}switch")
        for switch in switches:
            self._split_languages_in_switch(switch, ctx)

    def _split_languages_in_switch(self, switch: etree._Element, ctx: PreparationContext) -> None:
        # collect children first to avoid modifying while iterating
        children = list(switch)

        # Phase 1: validate everything up front (structure + duplicate
        # languages). If anything is wrong this raises and switch is left
        # completely untouched.
        entries = self._validate_switch_languages(children)

        # Phase 2: perform the actual split/clone. No validation or raising
        # happens from this point on — entries is already known to be valid.
        for text_el, real_langs in entries:
            if len(real_langs) == 1:
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

    def _validate_switch_languages(self, children: list[etree._Element]) -> list[tuple[etree._Element, list[str]]]:
        """
        Validate every child of a <switch> element and, for each valid
        <text> element, compute the normalized list of languages it
        declares.

        This is a pure read-only pass: it never mutates any element. It
        raises SvgStructureError on:
          - non-whitespace text content directly inside <switch>
            (i.e. on a non-element child such as a comment)
          - a child that is not a <text> element
          - the same language declared twice within one <text> element
          - the same language declared by two different <text> elements
            (including "fallback" for elements without systemLanguage)

        Comment nodes (and other non-element nodes with only whitespace
        content) are silently skipped.

        Returns a list of (text_el, real_langs) tuples, in document order,
        for every valid <text> child. real_langs is ["fallback"] for
        elements without a systemLanguage attribute.
        """
        existing_langs: set[str] = set()
        entries: list[tuple[etree._Element, list[str]]] = []

        for text_el in children:
            # --- structural validation (merged from _validate_text_el_children) ---
            if not isinstance(text_el.tag, str):
                # ignore comments etc, but if there's text content outside elements, check whitespace
                if text_el.text and text_el.text.strip():
                    raise SvgStructureError(code="structure-error-switch-text-content-outside-text")
                continue
            if text_el.tag not in ({f"{{{SVG_NS}}}text", "text"}):
                raise SvgStructureError(code="structure-error-switch-child-not-text")

            # --- language validation ---
            sys_lang = text_el.get("systemLanguage")
            real_langs = split_lang_list(sys_lang) if sys_lang else ["fallback"]

            languages_present: set[str] = set()
            for extra_lang in real_langs:
                if extra_lang in languages_present:
                    raise SvgStructureError(code="structure-error-multiple-lang-in-text", extra=[extra_lang])

                languages_present.add(extra_lang)

                if extra_lang in existing_langs:
                    raise SvgStructureError(code="structure-error-multiple-text-same-lang", extra=[extra_lang])

            existing_langs.update(languages_present)
            entries.append((text_el, real_langs))

        return entries

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
