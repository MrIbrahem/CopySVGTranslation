""""""

from __future__ import annotations

import logging
from pathlib import Path

from .config import TranslationConfig
from .io import SvgDocument
from .utils import are_switches_sorted, sort_switch_texts

logger = logging.getLogger(__name__)
SVG_NS = "http://www.w3.org/2000/svg"


class SwitchOrderChecker:

    def __init__(
        self,
        config: TranslationConfig,
    ) -> None:
        self.config = config

    def are_switches_sorted(self, svg_path: Path | str) -> bool:
        """
        Return True if every <switch> in the file is already sorted.

        Used as a pre-check: if False, the file can be fixed with
        :meth:`sort_switches` and re-uploaded.
        """
        svg_path = Path(str(svg_path))
        if not svg_path.exists():
            logger.error(f"SVG file not found: {svg_path}")
            return False

        try:
            doc = SvgDocument.load(svg_path, config=self.config)
            root = doc.root
        except Exception as exc:
            logger.error("Failed to parse SVG file: %s", exc)
            return False

        if root is None:
            return False

        return are_switches_sorted(root)

    def sort_switches(self, svg_path: Path | str, *, save_path: Path | None = None) -> bool:
        """
        Sort every <switch> in the file in place and optionally save it.

        Returns True if the file was modified (i.e. it was not already sorted).
        """
        doc: SvgDocument = SvgDocument.load(svg_path, config=self.config)
        root = doc.root
        tree = doc.tree

        if root is None or tree is None:
            return False

        # Already correctly ordered -> nothing to do (load once, no second parse).
        if are_switches_sorted(root):
            return False

        for elem in root.findall(".//svg:switch", namespaces={"svg": SVG_NS}):
            sort_switch_texts(elem)

        if save_path is not None:
            doc.save(savepath=save_path)
        return True


__all__ = [
    "SwitchOrderChecker",
]
