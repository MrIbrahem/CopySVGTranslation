"""Helpers for injecting translations into SVG files."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Iterable, Mapping

from lxml import etree

from ..text_utils import extract_text_from_node, normalize_text
from .preparation import SvgStructureException, make_translation_ready

logger = logging.getLogger(__name__)

def get_target_path(
    output_file: Path | str | None,
    output_dir: Path | str | None,
    svg_path: Path,
) -> Path:
    """Determines the target path for the output SVG file.

    If an output file path is provided, it's used directly. Otherwise,
    the path is constructed from an output directory (or the source file's
    directory if not provided) and the source file's name. The necessary
    parent directories are created in the latter case.

    Args:
        output_file: The explicit path for the output file.
        output_dir: The directory to save the output file in.
        svg_path: The path to the original SVG file.

    Returns:
        The resolved path for the output file.
    """
    if output_file:
        target_path = Path(output_file)
        target_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        save_dir = output_dir or svg_path.parent
        target_path = Path(save_dir) / svg_path.name
        target_path.parent.mkdir(parents=True, exist_ok=True)

    return target_path

def generate_unique_id(base_id: str, lang: str, existing_ids: set[str]) -> str:
    """Generate a unique identifier by appending the language and a counter."""
    new_id = f"{base_id}-{lang}"

    # If the base ID with language is unique, use it
    if new_id not in existing_ids:
        return new_id

    # Otherwise, add numeric suffix until unique
    counter = 1
    while f"{new_id}-{counter}" in existing_ids:
        counter += 1

    return f"{new_id}-{counter}"


def load_all_mappings(mapping_files: Iterable[Path | str]) -> dict:
    """Load and merge translation mapping JSON files into a single dictionary."""
    all_mappings: dict = {}

    for mapping_file in mapping_files:
        mapping_path = Path(mapping_file)
        if not mapping_path.exists():
            logger.warning(f"Mapping file not found: {mapping_path}")
            continue

        try:
            with open(mapping_path, 'r', encoding='utf-8') as f:
                mappings = json.load(f)
        except Exception as exc:
            logger.error(f"Error loading mapping file {mapping_path}: {exc}")
            continue

        for key, value in mappings.items():
            all_mappings.setdefault(key, {}).update(value)

        logger.debug("Loaded mappings from %s, entries: %s", mapping_path, len(mappings))

    return all_mappings


def work_on_switches(
    root: etree._Element,
    existing_ids: set[str],
    mappings: Mapping,
    case_insensitive: bool = True,
    overwrite: bool = False,
) -> dict:
    """Process ``<switch>`` elements and insert or update translations."""
    svg_ns = {'svg': 'http://www.w3.org/2000/svg'}
    stats = {
        'all_languages': 0,
        'new_languages': 0,
        'processed_switches': 0,
        'inserted_translations': 0,
        'skipped_translations': 0,
        'updated_translations': 0,
    }

    switches = root.xpath('//svg:switch', namespaces=svg_ns)
    logger.debug(f"Found {len(switches)} switch elements")

    if not switches:
        logger.error("No switch elements found in SVG")

    all_mappings_title = mappings.get("title", {})
    all_mappings = mappings.get("new", mappings)

    all_languages = set()
    new_languages = set()

    for switch in switches:
        text_elements = switch.xpath('./svg:text', namespaces=svg_ns)
        if not text_elements:
            continue

        default_texts = None
        default_node = None

        for text_elem in text_elements:
            system_lang = text_elem.get('systemLanguage')
            if system_lang:
                continue

            text_contents = extract_text_from_node(text_elem)
            default_texts = [normalize_text(text, case_insensitive) for text in text_contents]
            default_node = text_elem
            break

        if not default_texts:
            continue

        for text in default_texts:
            if text[-4:].isdigit():
                year = text[-4:]
                key = text[:-4]
                if key in all_mappings_title:
                    translations = all_mappings_title[key]
                    all_mappings[text] = {lang: f"{value} {year}" for lang, value in translations.items()}

        # Determine translations for each text line
        available_translations = {}
        for text in default_texts:
            key = text.lower() if case_insensitive else text
            if key in all_mappings:
                available_translations[key] = all_mappings[key]
            else:
                logger.warning(f"No mapping for '{key}'")

        if not available_translations:
            continue

        existing_languages = {t.get('systemLanguage') for t in text_elements if t.get('systemLanguage')}
        all_languages.update(existing_languages)

        # We assume all texts share same set of languages
        all_langs = set()
        for data in available_translations.values():
            all_langs.update(data.keys())

        for lang in all_langs:
            if lang in existing_languages and not overwrite:
                stats['skipped_translations'] += 1
                continue

            # Create or update node
            if lang in existing_languages and overwrite:
                for text_elem in text_elements:
                    if text_elem.get('systemLanguage') != lang:
                        continue

                    tspans = text_elem.xpath('./svg:tspan', namespaces=svg_ns)
                    for i, tspan in enumerate(tspans):
                        english_text = default_texts[i]
                        lookup_key = english_text.lower() if case_insensitive else english_text
                        if english_text in available_translations and lang in available_translations[english_text]:
                            tspan.text = available_translations[english_text][lang]
                        elif lookup_key in available_translations and lang in available_translations[lookup_key]:
                            tspan.text = available_translations[lookup_key][lang]

                    stats['updated_translations'] += 1
                    break
                continue

            new_languages.add(lang)

            new_node = etree.Element(default_node.tag, attrib=default_node.attrib)
            new_node.set('systemLanguage', lang)
            original_id = default_node.get('id')
            if original_id:
                new_id = generate_unique_id(original_id, lang, existing_ids)
                new_node.set('id', new_id)
                existing_ids.add(new_id)

            tspans = default_node.xpath('./svg:tspan', namespaces=svg_ns)

            if tspans:
                for tspan in tspans:
                    new_tspan = etree.Element(tspan.tag, attrib=tspan.attrib)
                    english_text = normalize_text(tspan.text or "")
                    key = english_text.lower() if case_insensitive else english_text
                    translated = all_mappings.get(key, {}).get(lang, english_text)
                    new_tspan.text = translated

                    # Generate unique ID for tspan if needed
                    original_tspan_id = tspan.get('id')
                    if original_tspan_id:
                        new_tspan_id = generate_unique_id(original_tspan_id, lang, existing_ids)
                        new_tspan.set('id', new_tspan_id)
                        existing_ids.add(new_tspan_id)

                    new_node.append(new_tspan)

            else:
                english_text = normalize_text(default_node.text or "")
                key = english_text.lower() if case_insensitive else english_text
                new_node.text = all_mappings.get(key, {}).get(lang, english_text)

            switch.append(new_node)
            stats['inserted_translations'] += 1

        stats['processed_switches'] += 1

    stats["all_languages"] = len(all_languages)
    stats["new_languages"] = len(new_languages)

    return stats


def sort_switch_texts(elem):
    """
    Sort <text> elements inside each <switch> so that elements
    without systemLanguage attribute come last.
    """
    ns = {"svg": "http://www.w3.org/2000/svg"}

    # Iterate over all <switch> elements
    # Get all <text> elements
    texts = elem.findall("svg:text", namespaces=ns)

    # Separate those with systemLanguage and those without
    without_lang = [t for t in texts if t.get("systemLanguage") is None]

    # Clear switch content
    for t in without_lang:
        elem.remove(t)

    # Re-insert <text> elements: first with language, then without
    for t in without_lang:
        elem.append(t)

    return elem


def inject(
    svg_file_path: Path | str,
    mapping_files: Iterable[Path | str] | None = None,
    all_mappings: Mapping | None = None,
    case_insensitive: bool = True,
    output_file: Path | None = None,
    output_dir: Path | None = None,
    overwrite: bool = False,
    save_result: bool = False,
    return_stats: bool = False,
):
    """Inject translations into the provided SVG file."""

    svg_path = Path(svg_file_path)

    if not svg_path.exists():
        logger.error(f"SVG file not found: {svg_path}")
        error = {"error": "File not exists"}
        return (None, error) if return_stats else None

    if not all_mappings:
        mapping_files = list(mapping_files or [])
        all_mappings = load_all_mappings(mapping_files)

    if not all_mappings:
        logger.error("No valid mappings found")
        error = {"error": "No valid mappings found"}
        return (None, error) if return_stats else None

    logger.debug(f"Injecting translations into {svg_path}")

    # Parse SVG as XML
    try:
        tree, root = make_translation_ready(svg_path, write_back=False)
    except SvgStructureException as exc:
        error = {"error": str(exc)}
        return (None, error) if return_stats else None
    except OSError as exc:
        if str(exc) != "structure-error-nested-tspans-not-supported":
            logger.error("Failed to parse SVG file: %s", exc)
        error = {"error": str(exc)}
        return (None, error) if return_stats else None

    # Collect all existing IDs to ensure uniqueness
    # existing_ids = {elem.get('id') for elem in root.xpath('//*[@id]') if elem.get('id')}
    existing_ids = set(root.xpath('//@id'))

    stats = work_on_switches(
        root,
        existing_ids,
        all_mappings,
        case_insensitive=case_insensitive,
        overwrite=overwrite,
    )

    # Fix old <svg:switch> tags if present
    for elem in root.findall(".//svg:switch", namespaces={"svg": "http://www.w3.org/2000/svg"}):
        elem.tag = "switch"
        sort_switch_texts(elem)

    if save_result:
        try:
            target_path = get_target_path(output_file, output_dir, svg_path)
            tree.write(str(target_path), encoding='utf-8', xml_declaration=True, pretty_print=True)
            logger.debug(f"Saved modified SVG to {target_path}")
        except Exception as e:
            logger.error(f"Failed writing {svg_path.name}: {e}")
            tree = None

    logger.debug(f"Processed {stats['processed_switches']} switches")
    logger.debug(f"Inserted {stats['inserted_translations']} translations")
    logger.debug(f"Updated {stats['updated_translations']} translations")
    logger.debug(f"Skipped {stats['skipped_translations']} existing translations")

    if return_stats:
        return tree, stats

    return tree
