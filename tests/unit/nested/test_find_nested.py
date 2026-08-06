"""
Unit tests for CopySVGTranslation/nested/find_nested.py module.

Functions to test: fix_nested_file
"""

from __future__ import annotations

import warnings
from pathlib import Path

from CopySVGTranslation.nested import MatchFixNestedTags

SVG_NS = "http://www.w3.org/2000/svg"


def fix_nested_file(
    source_file: Path,
    new_path: Path | None = None,
    pretty_print: bool | None = None,
) -> bool:
    processer = MatchFixNestedTags(
        source_file,
        new_path,
        pretty_print=pretty_print,
        strategy="flatten",
    )

    return processer.fix_file()


def _svg(inner: str) -> str:
    return f'<svg xmlns="{SVG_NS}">{inner}</svg>'


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
