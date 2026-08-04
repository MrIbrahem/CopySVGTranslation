"""
Unit tests for CopySVGTranslation/nested_analyze/find_nested.py module.

Functions to test: flatten_text, fix_nested_tspans, fix_nested_file
"""

from __future__ import annotations

import warnings
from pathlib import Path

from lxml import etree

from CopySVGTranslation.nested_analyze.find_nested import (
    SVG_NS,
    fix_nested_file,
    fix_nested_tspans,
    flatten_text,
)


def _svg(inner: str) -> str:
    return f'<svg xmlns="{SVG_NS}">{inner}</svg>'


def _parse(svg: str) -> etree._Element:
    return etree.fromstring(svg.encode("utf-8"))


# ---------------------------------------------------------------------------
# flatten_text
# ---------------------------------------------------------------------------
class TestFlattenText:
    """Tests for the flatten_text helper."""

    def test_simple_text(self):
        """Element with only text, no children."""
        elem = etree.Element("tspan")
        elem.text = "Hello"
        assert flatten_text(elem) == "Hello"

    def test_text_with_children(self):
        """Text + child text + child tail should be concatenated in order."""
        parent = etree.Element("tspan")
        parent.text = "Before "
        child = etree.SubElement(parent, "tspan")
        child.text = "Middle"
        child.tail = " After"
        assert flatten_text(parent) == "Before Middle After"

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
        assert flatten_text(root) == "ABCDE"

    def test_empty_element(self):
        """Element with no text or children returns empty string."""
        elem = etree.Element("tspan")
        assert flatten_text(elem) == ""

    def test_none_text_parts(self):
        """None text/tail values are handled gracefully."""
        elem = etree.Element("tspan")
        elem.text = None
        child = etree.SubElement(elem, "tspan")
        child.text = None
        child.tail = None
        assert flatten_text(elem) == ""


# ---------------------------------------------------------------------------
# fix_nested_tspans
# ---------------------------------------------------------------------------
class TestFixNestedTspans:
    """Tests for the fix_nested_tspans function (flatten variant)."""

    def test_no_nested_tspans_unchanged(self):
        """Flat tspans should not be modified."""
        svg = _svg("""<text id="t1"><tspan id="s1">Hello</tspan><tspan id="s2">World</tspan></text>""")
        root = _parse(svg)
        fix_nested_tspans(root)
        tspans = root.findall(f".//{{{SVG_NS}}}tspan")
        assert len(tspans) == 2
        assert tspans[0].text == "Hello"
        assert tspans[1].text == "World"

    def test_nested_tspan_flattened(self):
        """Nested tspans should be flattened into the parent."""
        svg = _svg("""<text id="t1"><tspan><tspan style="font-weight: 700;">Bold</tspan> normal</tspan></text>""")
        root = _parse(svg)
        fix_nested_tspans(root)
        tspans = root.findall(f".//{{{SVG_NS}}}tspan")
        # After flattening, there should be only one tspan with all text
        assert len(tspans) == 1
        assert "Bold" in tspans[0].text
        assert "normal" in tspans[0].text

    def test_children_removed_after_flatten(self):
        """After flattening, the nested children should be removed."""
        svg = _svg("""<text id="t1"><tspan><tspan id="inner">Inner</tspan></tspan></text>""")
        root = _parse(svg)
        fix_nested_tspans(root)
        tspans = root.findall(f".//{{{SVG_NS}}}tspan")
        assert len(tspans) == 1
        # No child elements left
        assert len(list(tspans[0])) == 0

    def test_tail_cleared_after_flatten(self):
        """Tail of the outer tspan should be None after flattening."""
        svg = _svg("""<text id="t1"><tspan><tspan>Inner</tspan></tspan></text>""")
        root = _parse(svg)
        fix_nested_tspans(root)
        tspans = root.findall(f".//{{{SVG_NS}}}tspan")
        assert tspans[0].tail is None

    def test_custom_tag_parameter(self):
        """The tag parameter should target different element types."""
        svg = _svg("""<text id="t1"><tspan><a href="url">Link text</a></tspan></text>""")
        root = _parse(svg)
        fix_nested_tspans(root, tag="a")
        tspans = root.findall(f".//{{{SVG_NS}}}tspan")
        assert len(tspans) == 1
        assert "Link text" in tspans[0].text

    def test_empty_text_element(self):
        """Empty text elements should not crash."""
        svg = _svg("<text></text>")
        root = _parse(svg)
        result = fix_nested_tspans(root)
        assert result is not None


# ---------------------------------------------------------------------------
# fix_nested_file
# ---------------------------------------------------------------------------
class TestFixNestedFile:
    """Tests for the fix_nested_file function."""

    def test_fix_nested_file_creates_output(self, tmp_path: Path):
        """Should write a fixed SVG to the output path."""
        src = tmp_path / "input.svg"
        dst = tmp_path / "output.svg"
        src.write_text(
            _svg("""<text id="t1"><tspan><tspan style="font-weight: 700;">Bold</tspan></tspan></text>"""),
            encoding="utf-8",
        )
        result = fix_nested_file(src, dst)
        assert result is True
        assert dst.exists()
        content = dst.read_text(encoding="utf-8")
        assert "Bold" in content

    def test_fix_nested_file_no_new_path_warns(self, tmp_path: Path):
        """Calling without new_path should emit a DeprecationWarning."""
        src = tmp_path / "input.svg"
        src.write_text(
            _svg('<text id="t1"><tspan>Hello</tspan></text>'),
            encoding="utf-8",
        )
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            fix_nested_file(src)
            dep_warnings = [x for x in w if issubclass(x.category, DeprecationWarning)]
            assert len(dep_warnings) >= 1

    def test_fix_nested_file_invalid_xml(self, tmp_path: Path):
        """Invalid XML should return False."""
        src = tmp_path / "bad.svg"
        dst = tmp_path / "out.svg"
        src.write_text("not xml", encoding="utf-8")
        result = fix_nested_file(src, dst)
        assert result is False

    def test_fix_nested_file_source_not_found(self, tmp_path: Path):
        """Missing source file should return False."""
        result = fix_nested_file(tmp_path / "missing.svg", tmp_path / "out.svg")
        assert result is False

    def test_fix_nested_file_pretty_print(self, tmp_path: Path):
        """pretty_print parameter should be passed through."""
        src = tmp_path / "input.svg"
        dst = tmp_path / "output.svg"
        src.write_text(
            _svg('<text id="t1"><tspan>Hello</tspan></text>'),
            encoding="utf-8",
        )
        result = fix_nested_file(src, dst, pretty_print=True)
        assert result is True

    def test_fix_nested_file_also_fixes_a_tags(self, tmp_path: Path):
        """Should also fix nested <a> tags inside tspans."""
        src = tmp_path / "input.svg"
        dst = tmp_path / "output.svg"
        src.write_text(
            _svg("""<text id="t1"><tspan><a href="url">Link</a></tspan></text>"""),
            encoding="utf-8",
        )
        result = fix_nested_file(src, dst)
        assert result is True
        content = dst.read_text(encoding="utf-8")
        assert "Link" in content

    def test_fix_nested_file_overwrite_input(self, tmp_path: Path):
        """When new_path == source, the file should be overwritten in place."""
        src = tmp_path / "input.svg"
        src.write_text(
            _svg('<text id="t1"><tspan><tspan style="font-weight: 700;">Bold</tspan></tspan></text>'),
            encoding="utf-8",
        )
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            result = fix_nested_file(src)
        assert result is True
        content = src.read_text(encoding="utf-8")
        assert "Bold" in content
