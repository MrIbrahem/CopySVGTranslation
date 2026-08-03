"""
Unit tests for CopySVGTranslation/workflows.py module.

Functions to test: svg_translate_between_files, svg_inject_translations
"""

from __future__ import annotations

from pathlib import Path

from CopySVGTranslation.workflows import (
    svg_translate_between_files,
    svg_inject_translations,
)

SVG_NS = "http://www.w3.org/2000/svg"
SVG_NSMAP = {"svg": SVG_NS}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _wrap_svg(inner: str) -> str:
    return f'<?xml version="1.0" encoding="utf-8"?><svg xmlns="{SVG_NS}" version="1.1">{inner}</svg>'


def _write_svg(tmp_path: Path, inner: str, name: str = "test.svg") -> Path:
    p = tmp_path / name
    p.write_text(_wrap_svg(inner), encoding="utf-8")
    return p


# ===========================================================================
# svg_translate_between_files
# ===========================================================================


class TestSvgExtractAndInject:
    """Tests for the svg_translate_between_files workflow function."""

    def test_basic_extract_and_inject(self, tmp_path: Path):
        """Should extract translations from source and inject into target."""
        source = _write_svg(
            tmp_path,
            """
            <switch>
                <text id="t0"><tspan id="t0">Hello</tspan></text>
                <text id="t0-ar" systemLanguage="ar"><tspan id="t0-ar">مرحبا</tspan></text>
            </switch>
            """,
            name="source.svg",
        )
        target = _write_svg(
            tmp_path,
            """
            <switch>
                <text id="t1"><tspan id="t1">Hello</tspan></text>
            </switch>
            """,
            name="target.svg",
        )
        output = tmp_path / "output.svg"
        data_output = tmp_path / "data.json"

        tree = svg_translate_between_files(
            extract_file=source,
            inject_file=target,
            target_path=output,
            all_mappings_file=data_output,
            save_result=True,
        )

        assert tree is not None
        assert output.exists()
        # assert data_output.exists()

    def test_returns_none_on_missing_source(self, tmp_path: Path):
        """Should return None when the source file does not exist."""
        target = _write_svg(tmp_path, "<switch><text id='t0'><tspan id='t0'>Hi</tspan></text></switch>")

        tree = svg_translate_between_files(
            extract_file=tmp_path / "nonexistent.svg",
            inject_file=target,
        )

        assert tree is None


# ===========================================================================
# svg_inject_translations
# ===========================================================================


class TestSvgExtractAndInjects:
    """Tests for the svg_inject_translations workflow function."""

    def test_basic_inject_from_mapping(self, tmp_path: Path):
        """Should inject translations from a provided mapping dict."""
        target = _write_svg(
            tmp_path,
            """
            <switch>
                <text id="t0"><tspan id="t0">Hello</tspan></text>
            </switch>
            """,
        )
        output = tmp_path / "output.svg"

        translations = {
            "new": {
                "hello": {"ar": "مرحبا"},
            }
        }

        tree = svg_inject_translations(
            translations=translations,
            inject_file=target,
            save_result=True,
            target_path=output,
        )

        assert tree is not None
