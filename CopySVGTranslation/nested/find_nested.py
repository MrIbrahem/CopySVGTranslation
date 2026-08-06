from __future__ import annotations

import logging
from pathlib import Path

from .flattener import NestedTspanFlattener
from .nested_base import FixNestedTagsBase

logger = logging.getLogger(__name__)

SVG_NS = "http://www.w3.org/2000/svg"


class FixNestedTagsNew(FixNestedTagsBase):

    def _flatten_all(self, root, tag=None):

        # 1. Process nested tspans using Flattener
        flattener = NestedTspanFlattener(strategy="preserve_style", also_fix_a=True)
        flattener.process(root)
        return root


class FixNestedTags(FixNestedTagsBase):

    def _flatten_all(self, root, tag=None):

        # 1. Process nested tspans using Flattener
        flattener = NestedTspanFlattener(strategy="flatten", also_fix_a=True)
        flattener.process(root)
        return root


def fix_nested_file(
    source_file: Path,
    new_path: Path | None = None,
    pretty_print: bool | None = None,
) -> bool:
    processer = FixNestedTags(pretty_print=pretty_print)

    return processer.fix_file(
        source_file=source_file,
        new_path=new_path,
    )


def fix_nested_file_new(
    source_file: Path,
    new_path: Path | None = None,
    pretty_print: bool | None = None,
) -> bool:
    processer = FixNestedTagsNew(pretty_print=pretty_print)

    return processer.fix_file(
        source_file=source_file,
        new_path=new_path,
    )


__all__ = [
    "FixNestedTags",
    "fix_nested_file",
    "FixNestedTagsNew",
    "fix_nested_file_new",
]
