"""Utilities for extracting translation data from SVG files."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from lxml import etree

from ..config import TranslationConfig
from ..core import SwitchNode, TextNode
from ..core.mapping import TranslationMapping
from ..exceptions import SvgIOError, SvgParseError
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
        self.year_handler = YearTitleHandler(self.config)
        self.strategy = matching_strategy or CompositeMatchingStrategy()

    # ------------------------------------------------------------------
    # Per-switch logic
    # ------------------------------------------------------------------
    def _process_switch_legacy(
        self,
        switch: etree.Element,
        mapping: TranslationMapping,
    ) -> None:
        new_switch = SwitchNode(switch)
        # Return the default (no systemLanguage) text node, if any.
        default: TextNode | None = new_switch.default_text_node()
        if default is None:
            return

        # Find all text elements within this switch
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
        for x in default_texts:
            key = normalize_text(x, self.config.case_insensitive)
            mapping.new.setdefault(key, {})

        # Match every language node
        for node in new_switch.text_nodes():
            if node.is_fallback:
                continue
            lang = node.language
            if not lang:
                continue

            text_elem = node.element

            tspans = text_elem.xpath("./svg:tspan", namespaces=SVG_NS)
            if tspans:
                tspans_to_id = {
                    tspan.text.strip(): tspan.get("id")
                    for tspan in tspans
                    if tspan.text and tspan.text.strip() and tspan.get("id")
                }
                text_contents = [tspan.text.strip() for tspan in tspans if tspan.text]
            else:
                tspans_to_id = {}
                text_contents = [text_elem.text.strip()] if text_elem.text else [""]

            for text in text_contents:
                normalized_translation = normalize_text(text)
                base_id = tspans_to_id.get(text.strip(), "")
                if not base_id:
                    continue

                base_id = base_id.split("-")[0].strip()

                english_text = mapping.tspans_by_id.get(base_id) or mapping.tspans_by_id.get(base_id.lower())

                logger.debug(f"{base_id=}, {english_text=}")

                if not english_text:
                    continue

                # store_key = english_text if english_text in new_translations else english_text.lower()
                key = normalize_text(english_text, self.config.case_insensitive)
                mapping.add(
                    key,
                    lang,
                    normalized_translation,
                    case_insensitive=False,  # key already normalized
                )

    def extract_from_root(self, root: etree._Element) -> TranslationMapping:
        mapping = TranslationMapping()
        # Find all switch elements
        switches = root.xpath("//svg:switch", namespaces=SVG_NS)
        logger.debug("Found %d switch elements", len(switches))

        for switch_el in switches:
            # self._process_switch(SwitchNode(switch_el), mapping)
            self._process_switch_legacy(switch_el, mapping)

        if self.config.enable_year_titles and mapping.new:
            self.year_handler.build_templates(mapping)

        return mapping

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract(self, path: Path | str) -> TranslationMapping:
        """
        Extract translation strings from an SVG file into a structured dictionary.
        """
        logger.debug(f"Extracting translations from {path}")

        try:
            doc = SvgDocument.load(path, config=self.config)
        except FileNotFoundError as exc:
            logger.error(f"SVG file not found: {path}")
            raise SvgIOError(f"SVG file not found: {path}") from exc
        except (etree.XMLSyntaxError, OSError) as exc:
            logger.error(f"Failed to parse SVG file {path}: {exc}")
            raise SvgParseError(f"Failed to parse SVG file: {exc}") from exc

        return self.extract_from_root(doc.root)

    def extract_json(self, path: Path | str) -> dict[str, Any]:
        """
        Extract translation strings from an SVG file into a structured dictionary.
        """
        result = self.extract(path)

        return result.to_json()


__all__ = [
    "SVGTranslationExtractor",
]
