# extraction/extractor.py
from __future__ import annotations

import logging
from pathlib import Path

from lxml import etree

from ..config import TranslationConfig
from ..core.mapping import TranslationMapping
from ..core.switch_node import SwitchNode
from ..io.svg_document import SvgDocument
from ..titles import YearTitleHandler
from ..utils.text import normalize_text
from .strategies import CompositeMatchingStrategy, MatchingStrategy

logger = logging.getLogger(__name__)
SVG_NS = {"svg": "http://www.w3.org/2000/svg"}


class SVGTranslationExtractor:
    """
    Extract translations from an SVG into a TranslationMapping.
    """

    def __init__(
        self,
        config: TranslationConfig | None = None,
        matching_strategy: MatchingStrategy | None = None,
    ) -> None:
        self.config = config or TranslationConfig()
        self.strategy = matching_strategy or CompositeMatchingStrategy()
        self.year_handler = YearTitleHandler(self.config)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def extract(self, path: Path | str) -> TranslationMapping:
        """
        Load the SVG and return a TranslationMapping.
        Raises on fatal I/O or parse errors; returns an empty mapping
        when no switches/translations are found.
        """
        doc = SvgDocument.load(path, config=self.config)
        return self.extract_from_root(doc.root)

    def extract_from_root(self, root: etree._Element) -> TranslationMapping:
        mapping = TranslationMapping()
        switches = root.xpath("//svg:switch", namespaces=SVG_NS)
        logger.debug("Found %d switch elements", len(switches))

        for switch_el in switches:
            self._process_switch(SwitchNode(switch_el), mapping)

        if self.config.enable_year_titles and mapping.new:
            self.year_handler.build_templates(mapping)

        return mapping

    # ------------------------------------------------------------------
    # Per-switch logic
    # ------------------------------------------------------------------
    def _process_switch(
        self,
        switch: SwitchNode,
        mapping: TranslationMapping,
    ) -> None:
        default = switch.fallback()
        if default is None:
            return

        default_texts = default.texts(
            normalize=True,
            case_insensitive=self.config.case_insensitive,
        )
        if not any(default_texts):
            return

        # Record diagnostic id → text (optional)
        for tspan in default.tspans():
            tid = tspan.get("id")
            if tid and tspan.text and tspan.text.strip():
                mapping.tspans_by_id[tid] = tspan.text.strip()

        # Ensure keys exist in mapping.new
        for text in default_texts:
            key = normalize_text(text, self.config.case_insensitive)
            mapping.new.setdefault(key, {})

        # Match every language node
        for node in switch.text_nodes():
            if node.is_fallback:
                continue
            lang = node.language
            if not lang:
                continue

            matches = self.strategy.match(
                default,
                node,
                case_insensitive=self.config.case_insensitive,
            )
            for m in matches:
                key = normalize_text(m.default_text, self.config.case_insensitive)
                mapping.add(
                    key,
                    lang,
                    m.translated_text,
                    case_insensitive=False,  # key already normalized
                )
