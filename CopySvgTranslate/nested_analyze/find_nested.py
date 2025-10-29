from __future__ import annotations

import logging
from pathlib import Path
from lxml import etree

logger = logging.getLogger("CopySvgTranslate")
SVG_NS = "http://www.w3.org/2000/svg"


def flatten_text(elem):
    """Recursively collect text and tails preserving order."""
    text_parts = []
    if elem.text:
        text_parts.append(elem.text)
    for child in elem:
        text_parts.append(flatten_text(child))
        if child.tail:
            text_parts.append(child.tail)
    return "".join(text_parts)


def wrap_tspan_with_anchor(root):
    """Wrap <tspan> inside <a> when <a> was originally inside the <tspan>."""
    SVG_NS = "http://www.w3.org/2000/svg"
    NSMAP = {"svg": SVG_NS}

    for tspan in root.findall(".//svg:tspan", namespaces=NSMAP):
        anchors = tspan.findall(".//svg:a", namespaces=NSMAP)
        if not anchors:
            continue

        if len(anchors) > 1:
            flattened = flatten_text(tspan)
            for child in list(tspan):
                tspan.remove(child)
            tspan.text = flattened
            tspan.tail = None
            continue

        anchor = anchors[0]  # take the first <a>
        parent = tspan.getparent()
        index = parent.index(tspan)

        # Collect all text inside the <tspan> (including the <a> content)
        full_text = []
        for node in tspan.iter():
            if node.text:
                full_text.append(node.text)
            if node.tail:
                full_text.append(node.tail)
        combined_text = "".join(full_text).strip()

        # Create a new <a> element with same attributes
        new_anchor = etree.Element(anchor.tag, **anchor.attrib)
        new_tspan = etree.Element(tspan.tag, **tspan.attrib)
        new_tspan.text = combined_text
        new_anchor.append(new_tspan)

        # Replace old <tspan> with new <a>
        parent.remove(tspan)
        parent.insert(index, new_anchor)

    return root


def fix_nested_tspans(root, tag=None):
    """Flatten nested <tspan> elements while preserving text order and spacing."""
    tag = tag or "tspan"
    # Process all tspans that contain nested tspans
    for tspan in root.findall(f".//{{{SVG_NS}}}tspan"):
        nested = tspan.findall(f".//{{{SVG_NS}}}{tag}")
        if nested:
            flattened = flatten_text(tspan)
            for child in list(tspan):
                tspan.remove(child)
            tspan.text = flattened
            tspan.tail = None

    return root


def match_nested_tags(svg_file_path: Path) -> list:
    """Find <tspan> elements that contain nested <tspan> tags."""
    result = []
    svg_file_path = Path(svg_file_path)

    if not svg_file_path.exists():
        logger.error(f"File not exists: {svg_file_path}")
        return []

    parser = etree.XMLParser(remove_blank_text=True)

    try:
        tree = etree.parse(str(svg_file_path), parser)
    except (etree.XMLSyntaxError, OSError) as exc:
        logger.error(f"Failed to parse SVG file {svg_file_path}: {exc}")
        return []

    root = tree.getroot()

    if root is None:
        return []

    # Find all <tspan> elements
    tspans = root.findall(f".//{{{SVG_NS}}}tspan")
    for tspan in tspans:
        # Check if <tspan> has element children (nested tags)
        element_children = [c for c in tspan if isinstance(c.tag, str)]
        if element_children:
            # Add string representation of nested element to results
            result.append(etree.tostring(tspan, pretty_print=False).decode("utf-8"))

    return result


def fix_nested_file(svg_file_path: Path, new_path: Path):
    """
    !
    """
    # ---
    svg_file_path = Path(svg_file_path)
    new_path = Path(new_path)
    # ---
    parser = etree.XMLParser(remove_blank_text=False)
    # ---
    try:
        tree = etree.parse(str(svg_file_path), parser)
    except (etree.XMLSyntaxError, OSError) as exc:
        logger.error(f"Failed to parse SVG file {svg_file_path}: {exc}")
        return False
    # ---
    root = tree.getroot()
    # ---
    root = fix_nested_tspans(root)
    # ---
    root = fix_nested_tspans(root, "a")
    # ---
    try:
        new_path.write_text(
            etree.tostring(root, encoding="unicode", pretty_print=True),
            encoding="utf-8"
        )
        return True
    except Exception:
        logger.error(f"Failed to write fixed svg file to: {str(new_path)}")
    # ---
    return False
