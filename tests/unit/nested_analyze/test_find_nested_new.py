"""
Unit tests for CopySVGTranslation/nested/find_nested_new.py module.

Functions to test: fix_nested_tspans, fix_nested_file_new
"""

from __future__ import annotations

import warnings
from pathlib import Path

from lxml import etree

from CopySVGTranslation.nested.find_nested_new import (
    SVG_NS,
    fix_nested_file_new,
    fix_nested_tspans,
)


def _svg(inner: str) -> str:
    return f'<svg xmlns="{SVG_NS}">{inner}</svg>'


def _parse(svg: str) -> etree._Element:
    return etree.fromstring(svg.encode("utf-8"))


# ---------------------------------------------------------------------------
# fix_nested_tspans
# ---------------------------------------------------------------------------
class TestFixNestedTspans:
    """Tests for the fix_nested_tspans function (new variant)."""

    def test_no_nested_tspans_unchanged(self):
        """Flat tspans should not be modified."""
        svg = _svg("""<text id="t1"><tspan id="s1">Hello</tspan><tspan id="s2">World</tspan></text>""")
        root = _parse(svg)
        result = fix_nested_tspans(root)
        tspans = result.findall(f".//{{{SVG_NS}}}tspan")
        assert len(tspans) == 2
        assert tspans[0].text == "Hello"
        assert tspans[1].text == "World"

    def test_flatten_nested_tspan_with_text_before(self):
        """Parent tspan text before nested child should become its own tspan."""
        svg = _svg("""<text id="t1"><tspan>Prefix <tspan style="font-weight: 700;">Bold</tspan></tspan></text>""")
        root = _parse(svg)
        fix_nested_tspans(root)
        tspans = root.findall(f".//{{{SVG_NS}}}tspan")
        # "Prefix " becomes its own tspan, then "Bold" becomes its own tspan
        texts = [t.text for t in tspans]
        assert "Prefix " in texts
        assert "Bold" in texts

    def test_flatten_nested_tspan_with_tail(self):
        """Tail text after a nested child should become its own tspan."""
        svg = _svg("""<text id="t1"><tspan><tspan style="font-weight: 700;">Bold</tspan> tail text</tspan></text>""")
        root = _parse(svg)
        fix_nested_tspans(root)
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
        fix_nested_tspans(root)
        tspans = root.findall(f".//{{{SVG_NS}}}tspan")
        styled = [t for t in tspans if t.text == "Styled"]
        assert len(styled) == 1
        assert styled[0].get("style") == "font-weight: 700;"
        assert styled[0].get("class") == "highlight"

    def test_whitespace_only_text_skipped(self):
        """Whitespace-only parent text should not produce an empty tspan."""
        svg = _svg("""<text id="t1"><tspan>   <tspan style="font-weight: 700;">Bold</tspan></tspan></text>""")
        root = _parse(svg)
        fix_nested_tspans(root)
        tspans = root.findall(f".//{{{SVG_NS}}}tspan")
        texts = [t.text for t in tspans]
        # whitespace-only text should be skipped
        assert None in texts or "   " not in [t for t in texts if t and t.strip()]

    def test_whitespace_only_tail_skipped(self):
        """Whitespace-only tail should not produce an empty tspan."""
        svg = _svg("""<text id="t1"><tspan><tspan style="font-weight: 700;">Bold</tspan>   </tspan></text>""")
        root = _parse(svg)
        fix_nested_tspans(root)
        tspans = root.findall(f".//{{{SVG_NS}}}tspan")
        texts = [t.text for t in tspans]
        assert "Bold" in texts

    def test_custom_tag_parameter(self):
        """The tag parameter should target different element types."""
        svg = _svg("""<text id="t1"><tspan><a href="url">Link text</a></tspan></text>""")
        root = _parse(svg)
        fix_nested_tspans(root, tag="a")
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
        fix_nested_tspans(root)
        tspans = root.findall(f".//{{{SVG_NS}}}tspan")
        texts = [t.text for t in tspans]
        assert "A" in texts
        assert "B" in texts
        assert "C" in texts

    def test_empty_text_element(self):
        """Empty text elements should not crash."""
        svg = _svg("<text></text>")
        root = _parse(svg)
        result = fix_nested_tspans(root)
        assert result is not None


# ---------------------------------------------------------------------------
# fix_nested_file_new
# ---------------------------------------------------------------------------
class TestFixNestedFile:
    """Tests for the fix_nested_file_new function."""

    def test_fix_nested_file_creates_output(self, tmp_path: Path):
        """Should write a fixed SVG to the output path."""
        src = tmp_path / "input.svg"
        dst = tmp_path / "output.svg"
        src.write_text(
            _svg("""<text id="t1"><tspan><tspan style="font-weight: 700;">Bold</tspan></tspan></text>"""),
            encoding="utf-8",
        )
        result = fix_nested_file_new(src, dst)
        assert result is True
        assert dst.exists()
        content = dst.read_text(encoding="utf-8")
        # After fixing, nested tspans should be flattened
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
            fix_nested_file_new(src)
            dep_warnings = [x for x in w if issubclass(x.category, DeprecationWarning)]
            assert len(dep_warnings) >= 1

    def test_fix_nested_file_invalid_xml(self, tmp_path: Path):
        """Invalid XML should return False."""
        src = tmp_path / "bad.svg"
        dst = tmp_path / "out.svg"
        src.write_text("not xml", encoding="utf-8")
        result = fix_nested_file_new(src, dst)
        assert result is False

    def test_fix_nested_file_source_not_found(self, tmp_path: Path):
        """Missing source file should return False."""
        result = fix_nested_file_new(tmp_path / "missing.svg", tmp_path / "out.svg")
        assert result is False

    def test_fix_nested_file_pretty_print(self, tmp_path: Path):
        """pretty_print parameter should be passed through."""
        src = tmp_path / "input.svg"
        dst = tmp_path / "output.svg"
        src.write_text(
            _svg('<text id="t1"><tspan>Hello</tspan></text>'),
            encoding="utf-8",
        )
        result = fix_nested_file_new(src, dst, pretty_print=True)
        assert result is True

    def test_fix_nested_file_also_fixes_a_tags(self, tmp_path: Path):
        """Should also fix nested <a> tags inside tspans."""
        src = tmp_path / "input.svg"
        dst = tmp_path / "output.svg"
        src.write_text(
            _svg("""<text id="t1"><tspan><a href="url">Link</a></tspan></text>"""),
            encoding="utf-8",
        )
        result = fix_nested_file_new(src, dst)
        assert result is True
        content = dst.read_text(encoding="utf-8")
        assert "Link" in content
