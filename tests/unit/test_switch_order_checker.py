"""
Unit tests for CopySVGTranslation.switch_order_checker.SwitchOrderChecker.

The checker verifies that every <switch> keeps its fallback <text> (no
systemLanguage) last, and can fix files out of order so they render on
Wikimedia Commons.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from CopySVGTranslation.config import TranslationConfig
from CopySVGTranslation.switch_order_checker import SwitchOrderChecker

SVG_NS = "http://www.w3.org/2000/svg"


def _wrap_svg(inner: str) -> str:
    return f'<svg xmlns="{SVG_NS}" version="1.1">{inner}</svg>'


def _write_svg(tmp_path: Path, inner: str, name: str = "test.svg") -> Path:
    p = tmp_path / name
    p.write_text(_wrap_svg(inner), encoding="utf-8")
    return p


# A switch that is already correct: language texts before the fallback.
SORTED_INNER = """
    <switch>
        <text id="t1-ar" systemLanguage="ar">مرحبا</text>
        <text id="t1-fr" systemLanguage="fr">Bonjour</text>
        <text id="t1">Hello</text>
    </switch>
"""

# A switch with the fallback first — must be reported as unsorted.
UNSORTED_INNER = """
    <switch>
        <text id="t1">Hello</text>
        <text id="t1-ar" systemLanguage="ar">مرحبا</text>
    </switch>
"""


class TestAreSwitchesSorted:
    def test_sorted_file_returns_true(self, tmp_path: Path):
        svg = _write_svg(tmp_path, SORTED_INNER)
        checker = SwitchOrderChecker(TranslationConfig())

        assert checker.are_switches_sorted(svg) is True

    def test_unsorted_file_returns_false(self, tmp_path: Path):
        svg = _write_svg(tmp_path, UNSORTED_INNER)
        checker = SwitchOrderChecker(TranslationConfig())

        assert checker.are_switches_sorted(svg) is False

    def test_missing_file_returns_false(self, tmp_path: Path):
        svg = tmp_path / "does_not_exist.svg"
        checker = SwitchOrderChecker(TranslationConfig())

        assert checker.are_switches_sorted(svg) is False

    def test_file_with_no_switches_returns_true(self, tmp_path: Path):
        svg = _write_svg(tmp_path, '<text id="t1">Hello</text>')
        checker = SwitchOrderChecker(TranslationConfig())

        assert checker.are_switches_sorted(svg) is True

    def test_multiple_switches_one_unsorted_returns_false(self, tmp_path: Path):
        inner = f"{SORTED_INNER}{UNSORTED_INNER}"
        svg = _write_svg(tmp_path, inner)
        checker = SwitchOrderChecker(TranslationConfig())

        assert checker.are_switches_sorted(svg) is False


class TestSortSwitches:
    def test_does_not_modify_already_sorted_file(self, tmp_path: Path):
        svg = _write_svg(tmp_path, SORTED_INNER)
        checker = SwitchOrderChecker(TranslationConfig())

        modified = checker.sort_switches(svg)

        assert modified is False

    def test_fixes_unsorted_file_in_memory(self, tmp_path: Path):
        svg = _write_svg(tmp_path, UNSORTED_INNER)
        checker = SwitchOrderChecker(TranslationConfig())

        # Without a save_path the file on disk is untouched, but the method
        # still reports that a change would be required.
        modified = checker.sort_switches(svg)

        assert modified is True
        # Disk content is unchanged because no save_path was given.
        assert checker.are_switches_sorted(svg) is False

    def test_fixes_unsorted_file_and_saves(self, tmp_path: Path):
        svg = _write_svg(tmp_path, UNSORTED_INNER)
        out = tmp_path / "fixed.svg"
        checker = SwitchOrderChecker(TranslationConfig())

        modified = checker.sort_switches(svg, save_path=out)

        assert modified is True
        assert out.exists()
        # The saved file must be reported as sorted when re-checked.
        assert checker.are_switches_sorted(out) is True

    def test_saved_file_has_fallback_last(self, tmp_path: Path):
        svg = _write_svg(tmp_path, UNSORTED_INNER)
        out = tmp_path / "fixed.svg"
        checker = SwitchOrderChecker(TranslationConfig())
        checker.sort_switches(svg, save_path=out)

        from lxml import etree

        root = etree.parse(str(out)).getroot()
        switch = root.find(f".//{{{SVG_NS}}}switch")
        assert switch is not None
        texts = switch.findall(f"{{{SVG_NS}}}text")
        assert texts[-1].get("systemLanguage") is None

    def test_sort_returns_false_on_missing_file(self, tmp_path: Path):
        svg = tmp_path / "missing.svg"
        checker = SwitchOrderChecker(TranslationConfig())

        # are_switches_sorted short-circuits to False, so sort_switches
        # attempts the load and surfaces FileNotFoundError.
        with pytest.raises(FileNotFoundError):
            checker.sort_switches(svg)

    def test_sort_raises_on_unparseable_content(self, tmp_path: Path):
        # File exists but is not valid XML: are_switches_sorted returns False,
        # so sort_switches attempts the load and propagates the parse error.
        svg = tmp_path / "bad.svg"
        svg.write_text("<svg><switch>", encoding="utf-8")
        checker = SwitchOrderChecker(TranslationConfig())

        with pytest.raises(Exception):  # noqa: B017
            checker.sort_switches(svg)
