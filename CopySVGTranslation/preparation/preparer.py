"""Utilities to prepare SVG files for the injection phase."""

from __future__ import annotations

import copy
import logging
import re
from pathlib import Path

from lxml import etree

from ..config import TranslationConfig
from ..exceptions import SvgStructureExceptionError
from ..utils import normalize_lang
from .steps import (
    AssignIds,
    LoadDocument,
    NormalizeTspans,
    PreparationContext,
    PreparationStep,
    WrapTspans,
    # ReorderTexts,
    # SplitLanguages,
    ValidateStructure,
)
logger = logging.getLogger(__name__)

SVG_NS = "http://www.w3.org/2000/svg"
XMLNS_ATTR = "{http://www.w3.org/2000/xmlns/}xmlns"


def get_text_content(el: etree._Element) -> str:
    """Return concatenated text content of element (like DOM textContent)."""
    return "".join(el.itertext())


def _clone_element(el: etree._Element) -> etree._Element:
    """Deep-clone an element."""
    return copy.deepcopy(el)


class SvgPreparationPipeline:
    """
    Prepares an SVG file for the translation phase.

    Ensures structural invariants are met before translations are injected:
    - every <text> lives inside a <switch>
    - every piece of translatable text is wrapped in a <tspan>
    - every translatable node has a unique, normalized id
    - systemLanguage attributes are normalized and split (comma-separated
      values are expanded into cloned <text> nodes)
    - <text> elements inside each <switch> are deterministically ordered
    """

    def __init__(self, config: TranslationConfig | None = None) -> None:
        self.config = config or TranslationConfig()
        self.steps: list[PreparationStep] = [
            LoadDocument(config),
            ValidateStructure(config),
            NormalizeTspans(config),
            AssignIds(config),
            WrapTspans(config),
            # SplitLanguages(config),
            # ReorderTexts(config),
        ]
        self.path: Path
        self.tree: etree._ElementTree
        self.root: etree._Element
        self.existing_ids: set[str] = set()
        self.ids_in_use: list[int] = [0]
        self.translatable_nodes: list[etree._Element] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run_new(self, path: Path) -> tuple[etree._ElementTree[etree._Element], etree._Element]:
        ctx = PreparationContext(
            path=path,
            config=self.config,
            # id_manager=IdManager(),
        )
        for step in self.steps:
            step.execute(ctx)

        self.existing_ids: set[str] = ctx.existing_ids
        # self.ids_in_use: list[int] = ctx.ids_in_use
        self.translatable_nodes: list[etree._Element] = ctx.translatable_nodes

        return ctx.tree, ctx.root

    def run(self, source_file: Path) -> tuple[etree._ElementTree[etree._Element], etree._Element]:
        """Run all preparation steps and return the resulting tree and root."""
        # Reset per-run state to ensure idempotent behavior
        self.path = Path(str(source_file))
        self.tree: etree._ElementTree
        self.root: etree._Element

        self.ids_in_use: list[int] = [0]
        self.tree, self.root = self.run_new(self.path)

        # self._wrap_loose_text_into_tspans()
        self._clean_ids_and_remove_empty_nodes()
        self._rebuild_translatable_nodes()
        self._assign_missing_ids()
        self._process_text_elements()
        self._split_switch_languages()
        self._reorder_texts()

        return self.tree, self.root

    # ------------------------------------------------------------------
    # Step 3: id allocation helpers
    # ------------------------------------------------------------------
    def _allocate_trsvg_id(self) -> str:
        """Allocate a new unique ``trsvg`` identifier."""
        next_id = max(self.ids_in_use) if self.ids_in_use else 0
        while True:
            next_id += 1
            candidate = f"trsvg{next_id}"
            if candidate not in self.existing_ids:
                self.ids_in_use.append(next_id)
                self.existing_ids.add(candidate)
                return candidate

    def _allocate_clone_id(self, base_id: str | None, lang: str) -> str:
        """Allocate a unique identifier for a cloned ``<text>`` node."""
        if base_id and re.match(r"^trsvg[0-9]+$", base_id):
            return self._allocate_trsvg_id()
        if base_id:
            base_candidate = f"{base_id}-{lang}"
            candidate = base_candidate
            suffix = 1
            while candidate in self.existing_ids:
                suffix += 1
                candidate = f"{base_candidate}-{suffix}"
            self.existing_ids.add(candidate)
            return candidate
        return self._allocate_trsvg_id()


    def _clean_ids_and_remove_empty_nodes(self) -> None:
        """Normalize/validate ids on translatable nodes and drop empty nodes."""
        for node in list(self.translatable_nodes):
            node_id = node.get("id")
            if node_id is not None:
                original_id = node_id
                node_id = node_id.strip()
                if node_id != original_id:
                    self.existing_ids.discard(original_id)
                if not node_id:
                    node.attrib.pop("id", None)
                    node_id = None
                else:
                    node.set("id", node_id)
                    if "|" in node_id or "/" in node_id:
                        raise SvgStructureExceptionError("structure-error-invalid-node-id", node, [node_id])
                    m = re.match(r"^trsvg([0-9]+)$", node_id)
                    if m:
                        self.ids_in_use.append(int(m.group(1)))
                    if node_id.isdigit():
                        node.attrib.pop("id", None)
                        self.existing_ids.discard(node_id)
                        node_id = None
                    else:
                        self.existing_ids.add(node_id)
            # remove empty nodes with no children and no text
            if (not list(node)) and (not (node.text and node.text.strip())):
                node_id = node.get("id")
                if node_id:
                    self.existing_ids.discard(node_id)
                parent = node.getparent()
                if parent is not None:
                    parent.remove(node)
                # also remove from translatable_nodes list
                try:
                    self.translatable_nodes.remove(node)
                except ValueError:
                    pass

    def _rebuild_translatable_nodes(self) -> None:
        """Rebuild translatable_nodes after removals (tspans then texts)."""
        self.translatable_nodes = []
        self.translatable_nodes.extend(self.root.findall(".//{%s}tspan" % SVG_NS))
        self.translatable_nodes.extend(self.root.findall(".//{%s}text" % SVG_NS))

    def _assign_missing_ids(self) -> None:
        """Assign new ids where missing."""
        for node in self.translatable_nodes:
            if node.get("id") is None:
                new_id = self._allocate_trsvg_id()
                node.set("id", new_id)

    # ------------------------------------------------------------------
    # Step 5: <text> structural checks and <switch> wrapping
    # ------------------------------------------------------------------
    def _process_text_elements(self) -> None:
        """
        Second pass on <text> elements: reject '$N' placeholders, normalize
        systemLanguage, ensure each <text> is wrapped in a <switch>, move
        style up to the switch, and verify only <tspan> children are present.
        """
        texts = self.root.findall(".//{%s}text" % SVG_NS)
        for text in texts:
            content = get_text_content(text)
            if re.search(r"\$[0-9]+", content):
                raise SvgStructureExceptionError("structure-error-text-contains-dollar", text, [content])

            # normalize systemLanguage if present
            # if text.get("systemLanguage"):
            #     text.set("systemLanguage", normalize_lang(text.get("systemLanguage")))

            # normalize systemLanguage if present
            language_attr = text.get("systemLanguage")
            if language_attr:
                normalized = ",".join(
                    normalize_lang(part) for part in re.split(r"\s*,\s*", language_attr.strip()) if part
                )
                text.set("systemLanguage", normalized)

            parent = text.getparent()
            if parent is None or (parent.tag not in ({f"{{{SVG_NS}}}switch", "switch"})):
                # Create a switch element in the SVG namespace and move the text into it
                switch = etree.Element("{%s}switch" % SVG_NS)
                parent_of_text = parent
                if parent_of_text is None:
                    raise SvgStructureExceptionError("structure-error-no-parent-for-text", text, text)
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
                    raise SvgStructureExceptionError("structure-error-non-tspan-inside-text", child, child)

    # ------------------------------------------------------------------
    # Step 6: <switch> language splitting
    # ------------------------------------------------------------------
    def _split_switch_languages(self) -> None:
        """Split comma-separated systemLanguage values into cloned <text> nodes."""
        switches = self.root.findall(".//{%s}switch" % SVG_NS)
        for sw in switches:
            # gather existing languages for duplicate detection
            existing_langs: set[str] = set()
            # collect children first to avoid modifying while iterating
            children = list(sw)
            for child in children:
                if not isinstance(child.tag, str):
                    # ignore comments etc, but if there's text content outside elements, check whitespace
                    if (child.text or "").strip():
                        raise SvgStructureExceptionError(
                            "structure-error-switch-text-content-outside-text", child, child
                        )
                    continue
                if child.tag not in ({f"{{{SVG_NS}}}text", "text"}):
                    raise SvgStructureExceptionError("structure-error-switch-child-not-text", child, child)

                language_attr = child.get("systemLanguage")
                real_langs = re.split(r",\s*", language_attr) if language_attr else ["fallback"]

                languages_present: set[str] = set()
                for real in real_langs:
                    if real in languages_present:
                        raise SvgStructureExceptionError("structure-error-multiple-lang-in-text", child, [real])
                    languages_present.add(real)
                    if real in existing_langs:
                        raise SvgStructureExceptionError("structure-error-multiple-text-same-lang", sw, [real])

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
                        raise SvgStructureExceptionError("structure-error-multiple-text-same-lang", sw, [real])
                    cloned = _clone_element(child)
                    if real == "fallback":
                        cloned.attrib.pop("systemLanguage", None)
                    else:
                        cloned.set("systemLanguage", real)
                    new_id = self._allocate_clone_id(base_id, real)
                    cloned.set("id", new_id)
                    existing_langs.add(real)
                    sw.append(cloned)

    # ------------------------------------------------------------------
    # Step 7: final ordering
    # ------------------------------------------------------------------
    def _reorder_texts(self) -> None:
        """
        Simple deterministic reordering: for every <switch>, sort child <text>
        elements by the numeric part of their id if present, otherwise keep
        original order. 'fallback' (no systemLanguage) is placed last.
        """
        switches = self.root.findall(".//{%s}switch" % SVG_NS)
        for sw in switches:
            texts = [c for c in sw if isinstance(c.tag, str) and c.tag in ({f"{{{SVG_NS}}}text", "text"})]

            def sort_key(el):
                lang = el.get("systemLanguage") or "fallback"
                m = re.search(r"trsvg(\d+)", (el.get("id") or ""))
                num = int(m.group(1)) if m else 10**9
                return (0 if lang == "fallback" else 1, num, lang)

            texts_sorted = sorted(texts, key=sort_key)
            # re-append in sorted order, leaving non-text children (if any) as-is
            for t in texts_sorted:
                sw.remove(t)
            for t in texts_sorted:
                sw.append(t)


def make_translation_ready(source_file: Path | str) -> tuple[etree._ElementTree, etree._Element]:
    """
    Legacy function-style wrapper around SvgPreparationPipeline, kept for
    backward compatibility with existing callers.
    """
    return SvgPreparationPipeline().run(source_file)


__all__ = [
    "SvgPreparationPipeline",
    "make_translation_ready",
]
