"""Helpers for injecting translations into SVG files."""

from __future__ import annotations

import json
import logging
from collections.abc import Iterable
from pathlib import Path

from lxml import etree

logger = logging.getLogger(__name__)


def file_langs(
    file: Path | str | etree._ElementTree | etree._Element | None,
) -> set[str]:
    """Return the list of languages declared in ``systemLanguage`` attributes."""

    languages: set[str] = set()
    root: etree._Element | None = None

    try:
        if isinstance(file, etree._ElementTree):
            root = file.getroot()
        elif isinstance(file, etree._Element):
            root = file
        elif file is not None:
            svg_path = Path(str(file))
            parser = etree.XMLParser(remove_blank_text=True)
            tree = etree.parse(str(svg_path), parser)
            root = tree.getroot()

        if root is None:
            return set()

        text_elements = root.xpath(
            ".//svg:text",
            namespaces={"svg": "http://www.w3.org/2000/svg"},
        )
        for text in text_elements:
            system_language = text.get("systemLanguage")
            if system_language:
                languages.add(system_language)
    except (etree.XMLSyntaxError, OSError):
        logger.exception(f"Error parsing SVG file: {file}")

    return languages


def get_target_path(
    output_file: Path | str | None,
    output_dir: Path | str | None,
    inject_path: Path,
) -> Path:
    """
    Determine the filesystem path where the modified SVG should be written.

    If `output_file` is provided, it is used as the target path. Otherwise the path is constructed by combining `output_dir` (if given) or the source file's directory with the source file's name. In all cases the parent directories for the resolved path are created if they do not exist.

    Parameters:
        output_file (Path | str | None): Explicit output file path to use.
        output_dir (Path | str | None): Directory to place the output file when `output_file` is not provided.
        inject_path (Path): Path to the original SVG file; its name is used when constructing a target path.

    Returns:
        Path: The resolved filesystem path for the output SVG file.
    """
    if output_dir:
        output_dir = Path(str(output_dir))

    if output_file:
        target_path = Path(str(output_file))
    else:
        save_dir = output_dir or inject_path.parent
        target_path = save_dir / inject_path.name
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
        mapping_path = Path(str(mapping_file))

        if not mapping_path.exists():
            logger.warning(f"Mapping file not found: {mapping_path}")
            continue

        try:
            with open(mapping_path, "r", encoding="utf-8") as f:
                mappings = json.load(f)
        except Exception as exc:
            logger.error(f"Error loading mapping file {mapping_path}: {exc}")
            continue

        for key, value in mappings.items():
            all_mappings.setdefault(key, {}).update(value)

        logger.debug("Loaded mappings from %s, entries: %s", mapping_path, len(mappings))

    return all_mappings


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


__all__ = [
    "file_langs",
    "get_target_path",
    "generate_unique_id",
    "load_all_mappings",
    "sort_switch_texts",
]
