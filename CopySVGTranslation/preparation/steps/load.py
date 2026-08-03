# injection/steps/load.py
from __future__ import annotations

import re

from lxml import etree

from ...exceptions import SvgStructureExceptionError
from .base import PreparationContext, PreparationStep

SVG_NS = "http://www.w3.org/2000/svg"
XMLNS_ATTR = "{http://www.w3.org/2000/xmlns/}xmlns"


class LoadDocument(PreparationStep):
    def execute(self, ctx: PreparationContext) -> None:
        """Parse the SVG file and ensure it has a sane default namespace."""
        if not ctx.path.exists():
            raise FileNotFoundError(f"SVG file not found: {ctx.path}")

        parser = etree.XMLParser(remove_blank_text=True)
        ctx.tree = etree.parse(str(ctx.path), parser)
        ctx.root = ctx.tree.getroot()
        if ctx.root is None:
            raise SvgStructureExceptionError("structure-error-no-doc-element")

        # Ensure default namespace (xmlns) exists and is sane
        default_ns = ctx.root.nsmap.get(None)
        if default_ns is None or re.match(r"^(&[^;]+;)+$", str(default_ns)):
            ctx.root.set(XMLNS_ATTR, SVG_NS)
