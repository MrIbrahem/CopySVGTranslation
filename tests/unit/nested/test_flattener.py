"""
Unit tests for CopySVGTranslation/nested/flattener.py module.
"""

from __future__ import annotations

from lxml import etree

from CopySVGTranslation.nested.flattener import (
    NestedTspanFlattener,
    _flatten_text,
)

SVG_NS = "http://www.w3.org/2000/svg"


def _svg(inner: str) -> str:
    return f'<svg xmlns="{SVG_NS}">{inner}</svg>'


def _parse(svg: str) -> etree._Element:
    return etree.fromstring(svg.encode("utf-8"))


# ---------------------------------------------------------------------------
# _flatten_text
# ---------------------------------------------------------------------------
class TestFlattenText:
    """Tests for the _flatten_text helper."""

    def test_simple_text(self):
        """Element with only text, no children."""
        elem = etree.Element("tspan")
        elem.text = "Hello"
        assert _flatten_text(elem) == "Hello"

    def test_text_with_children(self):
        """Text + child text + child tail should be concatenated in order."""
        parent = etree.Element("tspan")
        parent.text = "Before "
        child = etree.SubElement(parent, "tspan")
        child.text = "Middle"
        child.tail = " After"
        assert _flatten_text(parent) == "Before Middle After"

    def test_deeply_nested(self):
        """Deeply nested text should be collected recursively."""
        root = etree.Element("tspan")
        root.text = "A"
        child = etree.SubElement(root, "tspan")
        child.text = "B"

        grandchild = etree.SubElement(child, "tspan")
        grandchild.text = "C"  # pyright: ignore[reportAttributeAccessIssue]
        grandchild.tail = "D"
        child.tail = "E"
        assert _flatten_text(root) == "ABCDE"

    def test_empty_element(self):
        """Element with no text or children returns empty string."""
        elem = etree.Element("tspan")
        assert _flatten_text(elem) == ""

    def test_none_text_parts(self):
        """None text/tail values are handled gracefully."""
        elem = etree.Element("tspan")
        elem.text = None
        child = etree.SubElement(elem, "tspan")
        child.text = None
        child.tail = None
        assert _flatten_text(elem) == ""


# ---------------------------------------------------------------------------
# preserve_style/split_nested_tspans strategy
# ---------------------------------------------------------------------------
class TestSplitNestedTspansStrategy:
    """Tests for the preserve_style/split_nested_tspans strategy."""

    def preserve_style(self, root, tag=None):
        """
        Flatten nested <tspan> elements while preserving text order and spacing.
        """
        flattener = NestedTspanFlattener(strategy="split_nested_tspans", also_fix_a=True)
        flattener.process(root)
        return root

    def test_no_nested_tspans_unchanged(self):
        """Flat tspans should not be modified."""
        svg = _svg("""<text id="t1"><tspan id="s1">Hello</tspan><tspan id="s2">World</tspan></text>""")
        root = _parse(svg)
        result = self.preserve_style(root)
        tspans = result.findall(f".//{{{SVG_NS}}}tspan")
        assert len(tspans) == 2
        assert tspans[0].text == "Hello"
        assert tspans[1].text == "World"

    def test_flatten_nested_tspan_with_text_before(self):
        """Parent tspan text before nested child should become its own tspan."""
        svg = _svg("""<text id="t1"><tspan>Prefix <tspan style="font-weight: 700;">Bold</tspan></tspan></text>""")
        root = _parse(svg)
        self.preserve_style(root)
        tspans = root.findall(f".//{{{SVG_NS}}}tspan")
        # "Prefix " becomes its own tspan, then "Bold" becomes its own tspan
        texts = [t.text for t in tspans]
        assert "Prefix " in texts
        assert "Bold" in texts

    def test_flatten_nested_tspan_with_tail(self):
        """Tail text after a nested child should become its own tspan."""
        svg = _svg("""<text id="t1"><tspan><tspan style="font-weight: 700;">Bold</tspan> tail text</tspan></text>""")
        root = _parse(svg)
        self.preserve_style(root)
        tspans = root.findall(f".//{{{SVG_NS}}}tspan")
        texts = [t.text for t in tspans]
        assert "Bold" in texts
        # Tail text preserves leading space
        assert any("tail text" in (t or "") for t in texts)

    def test_flatten_nested_tspan_preserves_attributes(self):
        """Nested child attributes should be copied to the new sibling tspan."""
        svg = _svg(
            '<text id="t1">'
            "<tspan>"
            '<tspan style="font-weight: 700;" class="highlight">Styled</tspan>'
            "</tspan>"
            "</text>"
        )
        root = _parse(svg)
        self.preserve_style(root)
        tspans = root.findall(f".//{{{SVG_NS}}}tspan")
        styled = [t for t in tspans if t.text == "Styled"]
        assert len(styled) == 1
        assert styled[0].get("style") == "font-weight: 700;"
        assert styled[0].get("class") == "highlight"

    def test_whitespace_only_text_skipped(self):
        """Whitespace-only parent text should not produce an empty tspan."""
        svg = _svg("""<text id="t1"><tspan>   <tspan style="font-weight: 700;">Bold</tspan></tspan></text>""")
        root = _parse(svg)
        self.preserve_style(root)
        tspans = root.findall(f".//{{{SVG_NS}}}tspan")
        texts = [t.text for t in tspans]
        # whitespace-only text should be skipped
        assert None in texts or "   " not in [t for t in texts if t and t.strip()]

    def test_whitespace_only_tail_skipped(self):
        """Whitespace-only tail should not produce an empty tspan."""
        svg = _svg("""<text id="t1"><tspan><tspan style="font-weight: 700;">Bold</tspan>   </tspan></text>""")
        root = _parse(svg)
        self.preserve_style(root)
        tspans = root.findall(f".//{{{SVG_NS}}}tspan")
        texts = [t.text for t in tspans]
        assert "Bold" in texts

    def test_custom_tag_parameter(self):
        """The tag parameter should target different element types."""
        svg = _svg("""<text id="t1"><tspan><a href="url">Link text</a></tspan></text>""")
        root = _parse(svg)
        self.preserve_style(root, tag="a")
        tspans = root.findall(f".//{{{SVG_NS}}}tspan")
        # The <a> should be replaced with a tspan carrying the text
        texts = [t.text for t in tspans]
        assert "Link text" in texts

    def test_multiple_nested_children(self):
        """Multiple nested children should each become siblings."""
        svg = _svg(
            '<text id="t1">'
            "<tspan>"
            '<tspan id="a">A</tspan>'
            '<tspan id="b">B</tspan>'
            '<tspan id="c">C</tspan>'
            "</tspan>"
            "</text>"
        )
        root = _parse(svg)
        self.preserve_style(root)
        tspans = root.findall(f".//{{{SVG_NS}}}tspan")
        texts = [t.text for t in tspans]
        assert "A" in texts
        assert "B" in texts
        assert "C" in texts

    def test_empty_text_element(self):
        """Empty text elements should not crash."""
        svg = _svg("<text></text>")
        root = _parse(svg)
        result = self.preserve_style(root)
        assert result is not None

# ---------------------------------------------------------------------------
# flatten strategy
# ---------------------------------------------------------------------------
class TestFlattenStrategy:
    """Tests for the flatten strategy."""

    def flatten(self, root, tag=None):
        """
        Flatten nested <tspan> elements while preserving text order and spacing.
        """
        flattener = NestedTspanFlattener(strategy="flatten", also_fix_a=True)
        flattener.process(root)
        return root

    def test_no_nested_tspans_unchanged(self):
        """Flat tspans should not be modified."""
        svg = _svg("""<text id="t1"><tspan id="s1">Hello</tspan><tspan id="s2">World</tspan></text>""")
        root = _parse(svg)
        self.flatten(root)
        tspans = root.findall(f".//{{{SVG_NS}}}tspan")
        assert len(tspans) == 2
        assert tspans[0].text == "Hello"
        assert tspans[1].text == "World"

    def test_nested_tspan_flattened(self):
        """Nested tspans should be flattened into the parent."""
        svg = _svg("""<text id="t1"><tspan><tspan style="font-weight: 700;">Bold</tspan> normal</tspan></text>""")
        root = _parse(svg)
        self.flatten(root)
        tspans = root.findall(f".//{{{SVG_NS}}}tspan")
        # After flattening, there should be only one tspan with all text
        assert len(tspans) == 1
        assert "Bold" in tspans[0].text
        assert "normal" in tspans[0].text

    def test_children_removed_after_flatten(self):
        """After flattening, the nested children should be removed."""
        svg = _svg("""<text id="t1"><tspan><tspan id="inner">Inner</tspan></tspan></text>""")
        root = _parse(svg)
        self.flatten(root)
        tspans = root.findall(f".//{{{SVG_NS}}}tspan")
        assert len(tspans) == 1
        # No child elements left
        assert len(list(tspans[0])) == 0

    def test_tail_cleared_after_flatten(self):
        """Tail of the outer tspan should be None after flattening."""
        svg = _svg("""<text id="t1"><tspan><tspan>Inner</tspan></tspan></text>""")
        root = _parse(svg)
        self.flatten(root)
        tspans = root.findall(f".//{{{SVG_NS}}}tspan")
        assert tspans[0].tail is None

    def test_custom_tag_parameter(self):
        """The tag parameter should target different element types."""
        svg = _svg("""<text id="t1"><tspan><a href="url">Link text</a></tspan></text>""")
        root = _parse(svg)
        self.flatten(root, tag="a")
        tspans = root.findall(f".//{{{SVG_NS}}}tspan")
        assert len(tspans) == 1
        assert "Link text" in tspans[0].text

    def test_empty_text_element(self):
        """Empty text elements should not crash."""
        svg = _svg("<text></text>")
        root = _parse(svg)
        result = self.flatten(root)
        assert result is not None

