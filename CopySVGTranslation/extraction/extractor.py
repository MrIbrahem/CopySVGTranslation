"""Utilities for extracting translation data from SVG files."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from lxml import etree

from ..config import TranslationConfig
from ..core import SwitchNode
from ..core.mapping import TranslationMapping
from ..exceptions import SvgIOError, SvgParseError
from ..io.svg_document import SvgDocument
from ..titles import YearTitleHandler
from .header import AddTitlesTranslationsFromTitles, HeaderMappingExtractor
from .strategies import ByTspanIdStrategy, MatchingStrategy
from .switch_collector import SwitchTranslationCollector

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
        self.strategy = matching_strategy or ByTspanIdStrategy()
        self.collector = SwitchTranslationCollector(self.config, self.strategy)
        self.header_extractor = HeaderMappingExtractor(self.config, self.strategy)

    def extract_from_root(self, root: etree._Element) -> TranslationMapping:
        mapping = TranslationMapping()
        # Find all switch elements
        switches = root.xpath("//svg:switch", namespaces=SVG_NS)
        logger.debug("Found %d switch elements", len(switches))

        for switch_el in switches:
            self.collector.collect(SwitchNode(switch_el), mapping)

        if self.config.enable_year_titles and mapping.new:
            self.year_handler.build_templates(mapping)

        # Extract header-specific translations
        header = self.header_extractor.extract(root)
        if header:
            mapping.meta["header"] = header
            self.process_new_header_titles(mapping)

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

    def process_new_header_titles(self, mapping: TranslationMapping) -> None:
        """Insert new translations into the translations dictionary."""
        if not self.config.create_lang_template:
            return

        header = mapping.meta.get("header", {})
        extra_titles_new = self.year_handler.build_title_new_templates(header, create_lang_template=True)

        if not extra_titles_new:
            return

        # create new object with new titles, so we don't modify the original title_new or most likely overwrite it
        new_object = TranslationMapping.from_any({"title_new": extra_titles_new})

        adder = AddTitlesTranslationsFromTitles(new_object)
        adder.run()

        if adder.changes is False:
            return

        # Merge translations per-key, preserving existing language translations
        mapping.merge(new_object, merge_keys=["new"])


__all__ = [
    "SVGTranslationExtractor",
]
