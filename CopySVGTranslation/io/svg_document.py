# io/svg_document.py
from __future__ import annotations

import logging
from pathlib import Path

from lxml import etree

from ..config import TranslationConfig
from ..exceptions import SvgStructureError
from .svg_writer import write_svg

logger = logging.getLogger(__name__)

SVG_NS = "http://www.w3.org/2000/svg"
XMLNS_ATTR = "{http://www.w3.org/2000/xmlns/}xmlns"


class SvgDocument:
    """
    Thin I/O + document holder around an lxml ElementTree.

    Responsibilities:
    - Load an SVG from disk
    - Ensure a sane default namespace
    - Expose root / tree
    - Save back to disk
    """

    def __init__(
        self,
        tree: etree._ElementTree,
        path: Path | None = None,
        *,
        config: TranslationConfig | None = None,
    ) -> None:
        self.tree = tree
        self.path = path
        self.config = config or TranslationConfig()
        self.root = tree.getroot()
        if self.root is None:
            raise SvgStructureError(code="structure-error-no-doc-element")

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------
    @classmethod
    def load(
        cls,
        path: Path | str,
        *,
        config: TranslationConfig | None = None,
    ) -> SvgDocument:
        path = Path(path)
        config = config or TranslationConfig()

        if not path.exists():
            raise FileNotFoundError(f"SVG file not found: {path}")

        parser = etree.XMLParser(
            remove_blank_text=config.remove_blank_text,
            resolve_entities=False,
        )

        try:
            tree = etree.parse(str(path), parser)
        except (etree.XMLSyntaxError, OSError) as exc:
            logger.error("Failed to parse SVG %s: %s", path, exc)
            raise

        doc = cls(tree, path=path, config=config)
        doc._ensure_namespace()
        return doc

    # ------------------------------------------------------------------
    # Namespace helper
    # ------------------------------------------------------------------
    def _ensure_namespace(self) -> None:
        """Guarantee the document has a proper default SVG namespace."""
        import re

        default_ns = self.root.nsmap.get(None)
        if default_ns is None or re.match(r"^(&[^;]+;)+$", str(default_ns)):
            self.root.set(XMLNS_ATTR, SVG_NS)

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------
    def save(
        self,
        path: Path | str | None = None,
        *,
        pretty_print: bool | None = None,
        create_parents: bool | None = None,
    ) -> Path:
        target = Path(path) if path is not None else self.path
        if target is None:
            raise ValueError("No target path provided for save")

        target = write_svg(
            self.tree,
            target,
            config=self.config,
            pretty_print=pretty_print,
            create_parents=create_parents,
        )
        logger.debug("Saved SVG to %s", target)
        return target

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------
    def xpath(self, expression: str, namespaces: dict | None = None):
        ns = namespaces or {"svg": SVG_NS}
        return self.root.xpath(expression, namespaces=ns)

    def findall(self, tag: str):
        """Find all elements with the given local tag name in the SVG namespace."""
        return self.root.findall(f".//{{{SVG_NS}}}{tag}")


__all__ = [
    "SvgDocument",
]
