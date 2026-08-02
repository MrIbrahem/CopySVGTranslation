"""Helpers for injecting translations into SVG files."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from pathlib import Path

from lxml import etree

from ..titles_workers import get_new_titles_translations
from ..utils import (
    extract_text_from_node,
    file_langs,
    normalize_text,
    sort_switch_texts,
    tree_langs,
)
from ..utils.injection_utils import (
    generate_unique_id,
)
from .exceptions import (
    SvgNestedTspanExceptionError,
    SvgStructureExceptionError,
)
from .objects import InjectorData, InjectorStats
from .preparation import make_translation_ready

logger = logging.getLogger(__name__)


class SVGTranslationInjector:
    """Injects translations into SVG files."""

    def __init__(
        self,
        case_insensitive: bool = True,
        overwrite: bool = False,
        pretty_print: bool = True,
    ) -> None:
        """
        Parameters:
            case_insensitive (bool): If True, translation lookups are
                case-insensitive (keys are lowercased).
            overwrite (bool): If True, existing language nodes are updated
                in place instead of being skipped.
        """
        self.case_insensitive = case_insensitive
        self.overwrite = overwrite
        self.pretty_print = pretty_print
        self.result = InjectorData()
        self.new_stats: InjectorStats = self.result.new_stats

    def work_on_switches(
        self,
        root: etree._Element,
        existing_ids: set[str],
        mappings: Mapping,
    ) -> None:
        """Process ``<switch>`` elements and insert or update translations."""
        svg_ns = {"svg": "http://www.w3.org/2000/svg"}

        switches = root.xpath("//svg:switch", namespaces=svg_ns)
        logger.debug(f"Found {len(switches)} switch elements")

        if not switches:
            logger.error("No switch elements found in SVG")

        all_mappings_title = mappings.get("title", {})
        all_mappings_title_new = mappings.get("title_new", {})
        all_mappings = mappings.get("new", mappings)

        for switch in switches:
            text_elements = switch.xpath("./svg:text", namespaces=svg_ns)
            if not text_elements:
                continue

            default_texts = None
            default_node = None

            for text_elem in text_elements:
                system_lang = text_elem.get("systemLanguage")
                if system_lang:
                    continue

                text_contents = extract_text_from_node(text_elem)
                default_texts = [normalize_text(text, self.case_insensitive) for text in text_contents]
                default_node = text_elem
                break

            if not default_texts or default_node is None:
                continue

            new_titles_translations = get_new_titles_translations(all_mappings_title_new, default_texts)

            # all_mappings.update(titles_translations)
            # all_mappings.update(new_titles_translations)

            for key, translations in new_titles_translations.items():
                all_mappings.setdefault(key, {}).update(translations)

            # Determine translations for each text line
            available_translations = {}
            for text in default_texts:
                key = text.lower() if self.case_insensitive else text
                if key in all_mappings:
                    available_translations[key] = all_mappings[key]
                else:
                    logger.debug(f"No mapping for '{key}'")

            if not available_translations:
                continue

            existing_languages = {t.get("systemLanguage") for t in text_elements if t.get("systemLanguage")}

            # We assume all texts share same set of languages
            all_langs = set()
            for data in available_translations.values():
                all_langs.update(data.keys())

            for lang in all_langs:
                if lang in existing_languages and not self.overwrite:
                    self.new_stats.skipped_translations += 1
                    continue

                # Create or update node
                if lang in existing_languages and self.overwrite:
                    for text_elem in text_elements:
                        if text_elem.get("systemLanguage") != lang:
                            continue

                        tspans = text_elem.xpath("./svg:tspan", namespaces=svg_ns)
                        for i, tspan in enumerate(tspans):
                            english_text = default_texts[i]
                            lookup_key = english_text.lower() if self.case_insensitive else english_text
                            if english_text in available_translations and lang in available_translations[english_text]:
                                tspan.text = available_translations[english_text][lang]
                            elif lookup_key in available_translations and lang in available_translations[lookup_key]:
                                tspan.text = available_translations[lookup_key][lang]

                        self.new_stats.updated_translations += 1
                        break
                    continue

                new_node = etree.Element(default_node.tag, attrib=default_node.attrib)
                new_node.set("systemLanguage", lang)
                original_id = default_node.get("id")
                if original_id:
                    new_id = generate_unique_id(original_id, lang, existing_ids)
                    new_node.set("id", new_id)
                    existing_ids.add(new_id)

                tspans = default_node.xpath("./svg:tspan", namespaces=svg_ns)

                if tspans:
                    for tspan in tspans:
                        new_tspan = etree.Element(tspan.tag, attrib=tspan.attrib)
                        english_text = normalize_text(tspan.text or "")
                        key = english_text.lower() if self.case_insensitive else english_text
                        translated = all_mappings.get(key, {}).get(lang, english_text)
                        new_tspan.text = translated

                        # Generate unique ID for tspan if needed
                        original_tspan_id = tspan.get("id")
                        if original_tspan_id:
                            new_tspan_id = generate_unique_id(original_tspan_id, lang, existing_ids)
                            new_tspan.set("id", new_tspan_id)
                            existing_ids.add(new_tspan_id)

                        new_node.append(new_tspan)

                else:
                    english_text = normalize_text(default_node.text or "")
                    key = english_text.lower() if self.case_insensitive else english_text
                    new_node.text = all_mappings.get(key, {}).get(lang, english_text)

                switch.append(new_node)
                self.new_stats.inserted_translations += 1

            self.new_stats.processed_switches += 1

    def inject(
        self,
        inject_file: Path | str,
        all_mappings: Mapping | None = None,
        target_path: Path | None = None,
        save_result: bool = False,
    ) -> InjectorData:
        """Inject translations into the provided SVG file."""

        inject_path = Path(str(inject_file))

        if not inject_path.exists():
            logger.error(f"SVG file not found: {inject_path}")
            self.new_stats.error = "File does not exist"
            return self.result

        if not all_mappings:
            logger.error("No valid mappings found")
            self.new_stats.error = "No valid mappings found"
            return self.result

        logger.debug(f"Injecting translations into {inject_path}")

        # Parse SVG as XML
        try:
            tree, root = make_translation_ready(inject_path, write_back=False)
        except SvgNestedTspanExceptionError as exc:
            self.new_stats.error = "nested_tspan_error"
            return self.result

        except SvgStructureExceptionError as exc:
            self.new_stats.error = str(exc)
            return self.result

        except etree.XMLSyntaxError as exc:
            logger.error("Failed with XMLSyntaxError when parse SVG file: %s", exc)
            self.new_stats.error = str(exc)
            return self.result

        except (OSError, Exception) as exc:
            logger.error("Failed to parse SVG file: %s", exc)
            self.new_stats.error = str(exc)
            return self.result

        self.result.tree = tree
        # Collect all existing IDs to ensure uniqueness
        # existing_ids = {elem.get('id') for elem in root.xpath('//*[@id]') if elem.get('id')}
        existing_ids = set(root.xpath("//@id"))

        before_languages = file_langs(inject_path)

        self.work_on_switches(
            root,
            existing_ids,
            all_mappings,
        )

        # Fix old <svg:switch> tags if present
        for elem in root.findall(".//svg:switch", namespaces={"svg": "http://www.w3.org/2000/svg"}):
            elem.tag = "switch"
            sort_switch_texts(elem)

        after_languages = set()
        if save_result:
            try:
                tree.write(
                    str(target_path),
                    encoding="utf-8",
                    xml_declaration=True,
                    pretty_print=self.pretty_print,
                )
                after_languages = file_langs(target_path)
                logger.debug(f"Saved modified SVG to {target_path}")
            except Exception as e:
                logger.error(f"Failed writing {inject_path.name}: {e}")
                tree = None
        else:
            after_languages = tree_langs(tree)

        new_languages = after_languages - before_languages

        self.new_stats.all_languages = len(after_languages)
        self.new_stats.new_languages = len(new_languages)
        self.new_stats.new_languages_list = sorted(new_languages)

        logger.debug(f"Processed {self.new_stats.processed_switches} switches")
        logger.debug(f"Inserted {self.new_stats.inserted_translations} translations")
        logger.debug(f"Updated {self.new_stats.updated_translations} translations")
        logger.debug(f"Skipped {self.new_stats.skipped_translations} existing translations")

        return self.result


__all__ = [
    "SVGTranslationInjector",
]
