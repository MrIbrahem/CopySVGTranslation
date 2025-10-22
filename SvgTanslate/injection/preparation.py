"""Utilities to prepare SVG files for the injection phase."""

from __future__ import annotations

import copy
import logging
import re
from pathlib import Path
from typing import List, Tuple

from lxml import etree

logger = logging.getLogger(__name__)

SVG_NS = "http://www.w3.org/2000/svg"
XMLNS_ATTR = "{http://www.w3.org/2000/xmlns/}xmlns"


class SvgStructureException(Exception):
    """Raised when SVG structure is unsuitable for translation."""

    def __init__(self, code: str, element=None, extra=None):
        """Store structured error details for later reporting."""
        self.code = code
        self.element = element
        self.extra = extra
        msg = code
        if extra:
            msg += ": " + str(extra)
        super().__init__(msg)


def normalize_lang(lang: str) -> str:
    """Normalize a language tag to a simple IETF-like form."""
    if not lang:
        return lang
    pieces = re.split(r'[_\s]+', lang.strip())
    primary = pieces[0].lower()
    if len(pieces) > 1:
        rest = "-".join(p.upper() if len(p) == 2 else p.title() for p in pieces[1:])
        return f"{primary}-{rest}"
    return primary


def get_text_content(el: etree._Element) -> str:
    """Return concatenated text content of element (like DOM textContent)."""
    return "".join(el.itertext())


def clone_element(el: etree._Element) -> etree._Element:
    """Deep-clone an element."""
    return copy.deepcopy(el)


def reorder_texts(root: etree._Element):
    """Deterministically order ``<text>`` nodes within switches."""
    switches = root.findall(".//{%s}switch" % SVG_NS)
    for sw in switches:
        texts = [c for c in sw if isinstance(c.tag, str) and c.tag in ({f"{{{SVG_NS}}}text", "text"})]

        def sort_key(el):
            lang = el.get("systemLanguage") or "fallback"
            m = re.search(r'trsvg(\d+)', (el.get("id") or ""))
            num = int(m.group(1)) if m else 10**9
            return (0 if lang == "fallback" else 1, num, lang)

        texts_sorted = sorted(texts, key=sort_key)
        for t in texts_sorted:
            sw.remove(t)
        for t in texts_sorted:
            sw.append(t)


def make_translation_ready(svg_file_path: Path, write_back: bool = False) -> Tuple[etree._ElementTree, etree._Element]:
    """Prepare an SVG file for translation and return its tree and root."""
    parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(str(svg_file_path), parser)
    root = tree.getroot()
    if root is None:
        raise SvgStructureException('structure-error-no-doc-element')

    default_ns = root.nsmap.get(None)
    if default_ns is None or re.match(r'^(&[^;]+;)+$', str(default_ns)):
        root.set(XMLNS_ATTR, SVG_NS)

    texts = root.findall(".//{%s}text" % SVG_NS)
    if len(texts) == 0:
        logger.warning("File %s has nothing to translate", svg_file_path)
        return tree, root

    styles = root.findall(".//{%s}style" % SVG_NS)
    css_simple_re = re.compile(r'^([^{]+\{[^}]*\})*[^{]+$')
    for s in styles:
        css = (s.text or "")
        if '#' in css:
            if not css_simple_re.match(css):
                raise SvgStructureException('structure-error-css-too-complex', s)
            selectors = re.split(r'\{[^}]*\}', css)
            for selector in selectors:
                if '#' in selector:
                    raise SvgStructureException('structure-error-css-has-ids', s)

    trefs = root.findall(".//{%s}tref" % SVG_NS)
    if len(trefs) != 0:
        raise SvgStructureException('structure-error-contains-tref', trefs[0])

    ids_in_use: List[int] = [0]
    translatable_nodes: List[etree._Element] = []

    tspans = root.findall(".//{%s}tspan" % SVG_NS)
    for tspan in tspans:
        element_children = [c for c in tspan if isinstance(c.tag, str)]
        if len(element_children) == 0:
            translatable_nodes.append(tspan)
        else:
            raise SvgStructureException('structure-error-nested-tspans-not-supported', tspan)

    texts = root.findall(".//{%s}text" % SVG_NS)
    for text in texts:
        if (text.text or "").strip():
            tspan = etree.Element("{%s}tspan" % SVG_NS)
            tspan.text = text.text
            text.text = None
            text.insert(0, tspan)
            translatable_nodes.append(tspan)

        children = list(text)
        for idx, child in enumerate(children):
            if (child.tail or "").strip():
                new_tspan = etree.Element("{%s}tspan" % SVG_NS)
                new_tspan.text = child.tail
                child.tail = None
                insert_index = list(text).index(child) + 1
                text.insert(insert_index, new_tspan)
                translatable_nodes.append(new_tspan)

        translatable_nodes.append(text)

    for node in list(translatable_nodes):
        node_id = node.get("id")
        if node_id is not None:
            node_id = node_id.strip()
            node.set("id", node_id)
            if "|" in node_id or "/" in node_id:
                raise SvgStructureException('structure-error-invalid-node-id', node)
            m = re.match(r'^trsvg([0-9]+)$', node_id)
            if m:
                ids_in_use.append(int(m.group(1)))
            if node_id.isdigit():
                node.attrib.pop("id", None)
        if (not list(node)) and (not (node.text and node.text.strip())):
            parent = node.getparent()
            if parent is not None:
                parent.remove(node)
            try:
                translatable_nodes.remove(node)
            except ValueError:
                pass

    translatable_nodes = []

    return tree, root
