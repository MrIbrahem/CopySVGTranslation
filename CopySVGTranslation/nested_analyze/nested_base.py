from __future__ import annotations

from abc import ABC, abstractmethod
import logging
import warnings
from pathlib import Path

from lxml import etree

logger = logging.getLogger(__name__)

SVG_NS = "http://www.w3.org/2000/svg"


class FixNestedTagsBase(ABC):
    def __init__(self, pretty_print: bool | None = None) -> None:
        self.pretty_print = pretty_print

    @abstractmethod
    def _flatten_all(self, root, tag=None) -> None:
        ...

    def fix_file(self, source_file: Path, new_path: Path | None = None) -> bool:
        """
        !
        """
        # ---
        source_file = Path(source_file)
        if new_path is None:
            warnings.warn(
                "Calling fix_nested_file without new_path is deprecated. "
                "Pass an explicit output path to avoid overwriting the input file.",
                DeprecationWarning,
                stacklevel=2,
            )
        new_path = Path(new_path or source_file)
        # ---
        parser = etree.XMLParser(remove_blank_text=False)
        # ---
        try:
            tree = etree.parse(str(source_file), parser)
        except (etree.XMLSyntaxError, OSError) as exc:
            logger.error(f"Failed to parse SVG file {source_file}: {exc}")
            return False
        # ---
        root = tree.getroot()
        # ---
        if root is None:
            return False
        # ---
        root = self._flatten_all(root)
        # ---
        # NOTE: <a tags can also be nested inside <tspan>, so fix those too
        # https://svgtranslate.toolforge.org/ result: This file has unexpected content within a text element.
        # Only tspan elements should be used within text.
        root = self._flatten_all(root, "a")
        # ---
        try:
            _str = etree.tostring(
                root,
                encoding="unicode",
                pretty_print=self.pretty_print,
            )  # pyright: ignore[reportCallIssue]
            new_path.write_text(_str, encoding="utf-8")
            return True
        except Exception:
            logger.error(f"Failed to write fixed svg file to: {str(new_path)}")
        # ---
        return False


__all__ = [
    "FixNestedTagsBase",
]
