"""
TODO:
- Implement a function to transform the SVG text as described in the comments.

CopySVGTranslation/nested_analyze/find_nested_new.py

input:
<text x="16.0" y="581.0" style="font-size: 13px; line-height: 1.2;">
    <tspan x="16" y="581.0">
        <tspan style="font-weight: 700;">Data source:</tspan> United Nations Inter-agency Group for Child
        Mortality Estimation (2025)
    </tspan>
</text>

becomes this:

<text x="16.0" y="581.0" style="font-size: 13px; line-height: 1.2;">
    <tspan x="16" y="581.0">Data source: United Nations Inter-agency Group for Child Mortality Estimation (2025)</tspan>
</text>

but ideally it actually should be something like this:

<text x="16.0" y="581.0" style="font-size: 13px; line-height: 1.2;">
    <tspan style="font-weight: 700;">Data source: </tspan>
    <tspan>United Nations Inter-agency Group for Child Mortality Estimation (2025)</tspan>
</text>

tests for the above functionality are in tests/nested_analyze/test_fix_nested_file_new.py

pytest -m todo

"""

from __future__ import annotations

import logging
from pathlib import Path
from lxml import etree
from .nested_base import FixNestedTagsBase

logger = logging.getLogger(__name__)

SVG_NS = "http://www.w3.org/2000/svg"


class FixNestedTagsNew(FixNestedTagsBase):

    def fix_nested_tspans(self, root, tag=None):
        """
        Flatten nested <tspan> elements while preserving text order and spacing.

        For tspans with styled nested children, convert them to sibling tspans instead
        of flattening into a single tspan.
        """
        tag = tag or "tspan"

        # Find all parent elements that have tspan/tag children with nested content
        # We need to process from bottom-up to handle deeply nested structures
        for parent in root.findall(f".//{{{SVG_NS}}}text"):
            # Get direct tspan children of this text element
            direct_tspans = [child for child in parent if child.tag == f"{{{SVG_NS}}}tspan"]

            for tspan in direct_tspans:
                # Check if this tspan has nested children (direct children only)
                nested_children = [child for child in tspan if child.tag == f"{{{SVG_NS}}}{tag}"]

                if nested_children:
                    # Get the position of the current tspan in its parent
                    parent_list = list(parent)
                    tspan_index = parent_list.index(tspan)

                    # Collect all the new sibling tspans we'll create
                    new_siblings = []

                    # If the parent tspan has its own text before children, preserve it
                    # Note: We skip text that is only whitespace (e.g., indentation) as it's not
                    # semantically meaningful. Text with actual content is always preserved.
                    if tspan.text and tspan.text.strip():
                        text_tspan = etree.Element(f"{{{SVG_NS}}}tspan")
                        text_tspan.text = tspan.text
                        new_siblings.append(text_tspan)

                    # Process each nested child in order
                    for nested in nested_children:
                        # Clone the nested element (it becomes a sibling)
                        new_tspan = etree.Element(f"{{{SVG_NS}}}tspan")
                        # Copy all attributes from the nested element
                        for key, value in nested.attrib.items():
                            new_tspan.set(key, value)
                        # Copy the text content
                        new_tspan.text = nested.text
                        new_siblings.append(new_tspan)

                        # If the nested element has a tail, wrap it in a new tspan
                        # Note: We skip tail text that is only whitespace (e.g., indentation)
                        # as it's not semantically meaningful. Tail text with actual content is preserved.
                        if nested.tail and nested.tail.strip():
                            tail_tspan = etree.Element(f"{{{SVG_NS}}}tspan")
                            tail_tspan.text = nested.tail
                            new_siblings.append(tail_tspan)

                    # Remove the original tspan
                    parent.remove(tspan)

                    # Insert the new siblings at the position where the original tspan was
                    for i, sibling in enumerate(new_siblings):
                        parent.insert(tspan_index + i, sibling)

        return root

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

def fix_nested_tspans(root, tag=None):
    """
    Flatten nested <tspan> elements while preserving text order and spacing.
    """
    processer = FixNestedTagsNew()
    return processer.fix_nested_tspans(root, tag=tag)


__all__ = [
    "FixNestedTagsNew",
    "fix_nested_tspans",
    "fix_nested_file_new",
]
