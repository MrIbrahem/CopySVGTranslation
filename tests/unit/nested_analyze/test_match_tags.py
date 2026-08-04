"""
Unit tests for CopySVGTranslation/nested_analyze/match_tags.py module.

Functions to test: match_nested_tags
"""

from __future__ import annotations

from pathlib import Path


from CopySVGTranslation.nested_analyze.match_tags import (
    match_nested_tags,
)

SVG_NS = "http://www.w3.org/2000/svg"

def _svg(inner: str) -> str:
    return f'<svg xmlns="{SVG_NS}">{inner}</svg>'

# ---------------------------------------------------------------------------
# match_nested_tags
# ---------------------------------------------------------------------------
class TestMatchNestedTags:
    """Tests for the match_nested_tags function."""

    def test_finds_nested_tspans(self, tmp_path: Path):
        """Should detect tspans that contain nested tspans."""
        svg_path = tmp_path / "test.svg"
        svg_path.write_text(
            _svg("""<text id="t1"><tspan><tspan style="font-weight: 700;">Bold</tspan></tspan></text>"""),
            encoding="utf-8",
        )
        result = match_nested_tags(svg_path)
        assert len(result) >= 1

    def test_no_nested_tspans_returns_empty(self, tmp_path: Path):
        """Flat tspans should return an empty list."""
        svg_path = tmp_path / "test.svg"
        svg_path.write_text(
            _svg("""<text id="t1"><tspan id="s1">Hello</tspan></text>"""),
            encoding="utf-8",
        )
        result = match_nested_tags(svg_path)
        assert result == []

    def test_file_not_found_returns_empty(self, tmp_path: Path):
        """Non-existent file should return empty list."""
        result = match_nested_tags(tmp_path / "missing.svg")
        assert result == []

    def test_invalid_xml_returns_empty(self, tmp_path: Path):
        """Invalid XML file should return empty list."""
        svg_path = tmp_path / "bad.svg"
        svg_path.write_text("not xml at all <><>", encoding="utf-8")
        result = match_nested_tags(svg_path)
        assert result == []

    def test_returns_string_representations(self, tmp_path: Path):
        """Results should be string representations of tspan elements."""
        svg_path = tmp_path / "test.svg"
        svg_path.write_text(
            _svg("""<text id="t1"><tspan><tspan style="font-weight: 700;">Bold</tspan> text</tspan></text>"""),
            encoding="utf-8",
        )
        result = match_nested_tags(svg_path)
        assert len(result) >= 1
        assert "<tspan" in result[0]
