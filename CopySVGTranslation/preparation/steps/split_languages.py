# injection/steps/split_languages.py
from __future__ import annotations

import copy
import re

from lxml import etree

from ...exceptions import SvgStructureError
from ...utils import normalize_lang
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
        for sw in switches:
            # gather existing languages for duplicate detection
            existing_langs: set[str] = set()
            # collect children first to avoid modifying while iterating
            children = list(sw)
            for child in children:
                if not isinstance(child.tag, str):
                    # ignore comments etc, but if there's text content outside elements, check whitespace
                    if child.text and child.text.strip():
                        raise SvgStructureError("structure-error-switch-text-content-outside-text")
                    continue
                if child.tag not in ({f"{{{SVG_NS}}}text", "text"}):
                    raise SvgStructureError("structure-error-switch-child-not-text")

                language_attr = child.get("systemLanguage")
                real_langs = re.split(r",\s*", language_attr) if language_attr else ["fallback"]

                languages_present: set[str] = set()
                for real in real_langs:
                    if real in languages_present:
                        raise SvgStructureError("structure-error-multiple-lang-in-text", extra=[real])
                    languages_present.add(real)
                    if real in existing_langs:
                        raise SvgStructureError("structure-error-multiple-text-same-lang", extra=[real])

                if len(real_langs) == 1:
                    lang_value = real_langs[0]
                    if lang_value == "fallback":
                        if language_attr:
                            child.attrib.pop("systemLanguage", None)
                    else:
                        child.set("systemLanguage", lang_value)
                    existing_langs.add(lang_value)
                    continue

                original_lang = real_langs[0]
                if original_lang == "fallback":
                    child.attrib.pop("systemLanguage", None)
                else:
                    child.set("systemLanguage", original_lang)
                existing_langs.add(original_lang)

                base_id = child.get("id")
                for real in real_langs[1:]:
                    if real in existing_langs:
                        raise SvgStructureError("structure-error-multiple-text-same-lang", extra=[real])
                    cloned = _clone_element(child)
                    if real == "fallback":
                        cloned.attrib.pop("systemLanguage", None)
                    else:
                        cloned.set("systemLanguage", real)
                    new_id = self._allocate_clone_id(ctx, base_id, real)
                    cloned.set("id", new_id)
                    existing_langs.add(real)
                    sw.append(cloned)

    def _allocate_clone_id(self, ctx, base_id: str | None, lang: str) -> str:
        """Allocate a unique identifier for a cloned ``<text>`` node."""
        if base_id and re.match(r"^trsvg[0-9]+$", base_id):
            return self._allocate_trsvg_id(ctx)

        if base_id:
            base_candidate = f"{base_id}-{lang}"
            candidate = base_candidate
            suffix = 1
            while candidate in ctx.id_manager.existing_ids:
                suffix += 1
                candidate = f"{base_candidate}-{suffix}"
            ctx.id_manager.register(candidate)
            return candidate
        return self._allocate_trsvg_id(ctx)

    # ------------------------------------------------------------------
    # Step 3: id allocation helpers
    # ------------------------------------------------------------------
    def _allocate_trsvg_id(self, ctx) -> str:
        """Allocate a new unique ``trsvg`` identifier."""
        counter = 1

        while f"trsvg{counter}" in ctx.id_manager.existing_ids:
            counter += 1

        new_id = f"trsvg{counter}"
        # ctx.ids_in_use.append(counter)
        ctx.id_manager.register(new_id)
        return new_id
