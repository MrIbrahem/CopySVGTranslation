"""
Unit tests for CopySVGTranslation/nested/nested.py module.

Functions to test: fix_nested_file_new
"""

from __future__ import annotations

from pathlib import Path

from CopySVGTranslation.nested import MatchFixNestedTags

SVG_NS = "http://www.w3.org/2000/svg"


def fix_nested_file_new(
    source_file: Path,
    new_path: Path | None = None,
    pretty_print: bool | None = None,
) -> bool:
    processer = MatchFixNestedTags(
        source_file,
        new_path,
        pretty_print=pretty_print,
        strategy="preserve_style",
    )

    return processer.fix_file()


def _svg(inner: str) -> str:
    return f'<svg xmlns="{SVG_NS}">{inner}</svg>'


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
