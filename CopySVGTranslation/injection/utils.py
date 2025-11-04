"""Helpers for injecting translations into SVG files."""

from __future__ import annotations

import logging
from pathlib import Path

from lxml import etree

logger = logging.getLogger("CopySVGTranslation")


class SvgStructureException(Exception):
    """Raised when SVG structure is unsuitable for translation."""

    def __init__(self, code: str, element=None, extra=None):
        """Store structured error details for later reporting.

        Parameters:
            code (str): Machine-readable error code describing the structural
                issue encountered.
            element: Optional XML element related to the error (for diagnostics).
            extra: Optional supplemental data used to enrich the exception
                message.
        """
        self.code = code
        self.element = element
        self.extra = extra
        msg = code
        if extra:
            msg += ": " + str(extra)
        super().__init__(msg)


class SvgNestedTspanException(SvgStructureException):
    """Raised when encountering nested ``<tspan>`` elements."""

    def __init__(self, element=None, extra=None, node_text=None):
        self.node_text = node_text
        super().__init__("structure-error-nested-tspans-not-supported", element, extra)

    def node(self):
        return " ".join(self.node_text.strip().split())


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
            './/svg:text',
            namespaces={'svg': 'http://www.w3.org/2000/svg'},
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
