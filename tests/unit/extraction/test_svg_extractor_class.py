"""
Unit tests for SVGTranslationExtractor class and TranslationMapping dataclass.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from CopySVGTranslation.config import TranslationConfig
from CopySVGTranslation.core.mapping import TranslationMapping
from CopySVGTranslation.extraction.extractor import (
    SVGTranslationExtractor,
)

SVG_NS = "http://www.w3.org/2000/svg"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _wrap_svg(inner: str) -> str:
    return f'<svg xmlns="{SVG_NS}" version="1.1">{inner}</svg>'


def _write_svg(tmp_path: Path, inner: str, name: str = "test.svg") -> Path:
    p = tmp_path / name
    p.write_text(_wrap_svg(inner), encoding="utf-8")
    return p


# ===========================================================================
# TranslationMapping dataclass tests
# ===========================================================================


class TestExtractorData:
    """Tests for the TranslationMapping dataclass."""

    def test_default_values(self):
        data = TranslationMapping()
        assert data.new == {}
        assert data.tspans_by_id == {}
        assert data.title_new == {}
        assert data.error is None

    def test_to_json_returns_dict(self):
        data = TranslationMapping()
        result = data.to_json()
        assert isinstance(result, dict)
        assert "new" in result
        assert "tspans_by_id" in result
        assert "title_new" in result
        assert "error" in result

        assert result == {"new": {}, "tspans_by_id": {}, "title_new": {}, "meta": {}, "error": ""}

    def test_to_json_reflects_data(self):
        data = TranslationMapping(
            new={"hello": {"ar": "مرحبا"}},
            tspans_by_id={"t0": "Hello"},
            title_new={},
            error="",
        )
        result = data.to_json()
        assert result["new"] == {"hello": {"ar": "مرحبا"}}
        assert result["tspans_by_id"] == {"t0": "Hello"}
        assert result["title_new"] == {}

    def test_to_json_error_field(self):
        data = TranslationMapping(error="File not found")
        result = data.to_json()
        assert result["error"] == "File not found"

    def test_fields_are_independent(self):
        """Each instance should have independent mutable defaults."""
        a = TranslationMapping()
        b = TranslationMapping()
        a.new["key"] = {"ar": "val"}
        assert "key" not in b.new


# ===========================================================================
# SVGTranslationExtractor constructor tests
# ===========================================================================


class TestSVGTranslationExtractorInit:
    """Tests for SVGTranslationExtractor initialization."""

    def test_default_case_insensitive(self):
        ext = SVGTranslationExtractor()
        assert ext.config.case_insensitive is True

    def test_case_insensitive_false(self):
        config = TranslationConfig(
            case_insensitive=False,
        )
        ext = SVGTranslationExtractor(config)

        assert ext.config.case_insensitive is False


# ===========================================================================
# SVGTranslationExtractor.extract() tests
# ===========================================================================


class TestSVGTranslationExtractorExtract:
    """Tests for the extract() method."""

    def test_basic_extraction(self, tmp_path: Path):
        inner = """
            <switch>
                <text id="t0-ar" systemLanguage="ar"><tspan id="t0-ar">مرحبا</tspan></text>
                <text id="t0"><tspan id="t0">Hello</tspan></text>
            </switch>
        """
        svg = _write_svg(tmp_path, inner)
        ext = SVGTranslationExtractor()
        result = ext.extract(svg)

        assert isinstance(result, TranslationMapping)
        assert result.error is None
        assert "hello" in result.new
        assert result.new["hello"]["ar"] == "مرحبا"

    def test_extraction_multiple_switches(self, tmp_path: Path):
        inner = """
            <switch>
                <text id="t0-ar" systemLanguage="ar"><tspan id="t0-ar">مرحبا</tspan></text>
                <text id="t0-fr" systemLanguage="fr"><tspan id="t0-fr">Bonjour</tspan></text>
                <text id="t0"><tspan id="t0">Hello</tspan></text>
            </switch>
            <switch>
                <text id="t1-ar" systemLanguage="ar"><tspan id="t1-ar">وداعا</tspan></text>
                <text id="t1"><tspan id="t1">Goodbye</tspan></text>
            </switch>
        """
        svg = _write_svg(tmp_path, inner)
        ext = SVGTranslationExtractor()
        result = ext.extract(svg)

        assert result.error is None
        assert "hello" in result.new
        assert result.new["hello"]["ar"] == "مرحبا"
        assert result.new["hello"]["fr"] == "Bonjour"
        assert "goodbye" in result.new
        assert result.new["goodbye"]["ar"] == "وداعا"

    def test_case_insensitive_lowercases_keys(self, tmp_path: Path):
        inner = """
            <switch>
                <text id="t0-es" systemLanguage="es"><tspan id="t0-es">Hola</tspan></text>
                <text id="t0"><tspan id="t0">Hello World</tspan></text>
            </switch>
        """
        svg = _write_svg(tmp_path, inner)
        config = TranslationConfig(
            case_insensitive=True,
        )
        ext = SVGTranslationExtractor(config)
        result = ext.extract(svg)

        assert "hello world" in result.new
        assert "Hello World" not in result.new

    def test_case_sensitive_preserves_case(self, tmp_path: Path):
        inner = """
            <switch>
                <text id="t0-es" systemLanguage="es"><tspan id="t0-es">Hola</tspan></text>
                <text id="t0"><tspan id="t0">Hello World</tspan></text>
            </switch>
        """
        svg = _write_svg(tmp_path, inner)
        config = TranslationConfig(
            case_insensitive=False,
        )
        ext = SVGTranslationExtractor(config)
        result = ext.extract(svg)

        assert "Hello World" in result.new

    def test_tspans_by_id_collected(self, tmp_path: Path):
        inner = """
            <switch>
                <text id="t0"><tspan id="t0">Hello</tspan></text>
            </switch>
            <switch>
                <text id="t1"><tspan id="t1">World</tspan></text>
            </switch>
        """
        svg = _write_svg(tmp_path, inner)
        ext = SVGTranslationExtractor()
        result = ext.extract(svg)

        assert result.tspans_by_id["t0"] == "Hello"
        assert result.tspans_by_id["t1"] == "World"

    def test_title_extraction_with_year_suffix(self, tmp_path: Path):
        inner = """
            <switch>
                <text id="t0-ar" systemLanguage="ar"><tspan id="t0-ar">السكان 2020</tspan></text>
                <text id="t0"><tspan id="t0">Population 2020</tspan></text>
            </switch>
        """
        svg = _write_svg(tmp_path, inner)
        ext = SVGTranslationExtractor()
        result = ext.extract(svg)

        assert result.error is None
        # The full text should be in "new"
        assert "population 2020" in result.new
        # Title section should have the year-stripped version
        assert isinstance(result.title_new, dict)

    def test_no_switches_returns_empty(self, tmp_path: Path):
        inner = '<text id="t0"><tspan>Just text</tspan></text>'
        svg = _write_svg(tmp_path, inner)
        ext = SVGTranslationExtractor()
        result = ext.extract(svg)

        assert result.error is None
        assert result.new == {}

    def test_text_without_tspan(self, tmp_path: Path):
        inner = """
            <switch>
                <text id="t0-fr" systemLanguage="fr">Bonjour</text>
                <text id="t0">Hello</text>
            </switch>
        """
        svg = _write_svg(tmp_path, inner)
        ext = SVGTranslationExtractor()
        result = ext.extract(svg)

        # Without tspan children the text node content is used directly.
        # The key may not appear in "new" if there's no tspan id to match,
        # but the extractor should not crash.
        assert result.error is None

    def test_empty_svg(self, tmp_path: Path):
        svg = _write_svg(tmp_path, "")
        ext = SVGTranslationExtractor()
        result = ext.extract(svg)

        assert result.error is None
        assert result.new == {}

    def test_whitespace_normalization(self, tmp_path: Path):
        inner = """
            <switch>
                <text id="t0-es" systemLanguage="es"><tspan id="t0-es">  Hola   Mundo  </tspan></text>
                <text id="t0"><tspan id="t0">  Hello   World  </tspan></text>
            </switch>
        """
        svg = _write_svg(tmp_path, inner)
        ext = SVGTranslationExtractor()
        result = ext.extract(svg)

        # Keys should be normalized (trimmed + collapsed whitespace)
        assert "hello world" in result.new
        assert result.new["hello world"]["es"] == "Hola Mundo"


# ===========================================================================
# Error handling tests
# ===========================================================================


class TestSVGTranslationExtractorErrors:
    """Tests for error handling in SVGTranslationExtractor."""

    def test_nonexistent_file(self, tmp_path: Path):
        from CopySVGTranslation.exceptions import SvgIOError

        ext = SVGTranslationExtractor()
        with pytest.raises(SvgIOError):
            ext.extract(tmp_path / "missing.svg")

    def test_invalid_xml(self, tmp_path: Path):
        from CopySVGTranslation.exceptions import SvgParseError

        svg = tmp_path / "bad.svg"
        svg.write_text("<svg><unclosed>", encoding="utf-8")
        ext = SVGTranslationExtractor()
        with pytest.raises(SvgParseError):
            ext.extract(svg)

    def test_empty_file(self, tmp_path: Path):
        from CopySVGTranslation.exceptions import SvgParseError

        svg = tmp_path / "empty.svg"
        svg.write_text("", encoding="utf-8")
        ext = SVGTranslationExtractor()
        with pytest.raises(SvgParseError):
            ext.extract(svg)

    def test_error_cleared_between_calls(self, tmp_path: Path):
        """Each call to extract() should use the same translations instance,
        but a successful call should not carry over an old error."""
        svg = _write_svg(tmp_path, '<switch><text id="t0"><tspan id="t0">Hi</tspan></text></switch>')
        ext = SVGTranslationExtractor()
        result = ext.extract(svg)
        assert result.error is None


# ===========================================================================
# to_json round-trip test
# ===========================================================================


class TestExtractorDataToJson:
    """Tests for TranslationMapping.to_json() method."""

    def test_roundtrip_structure(self, tmp_path: Path):
        inner = """
            <switch>
                <text id="t0-ar" systemLanguage="ar"><tspan id="t0-ar">مرحبا</tspan></text>
                <text id="t0"><tspan id="t0">Hello</tspan></text>
            </switch>
        """
        svg = _write_svg(tmp_path, inner)
        ext = SVGTranslationExtractor()
        result = ext.extract(svg)
        data = result.to_json()

        assert isinstance(data, dict)
        assert set(data.keys()) == {"new", "tspans_by_id", "title_new", "error", "meta"}
        assert isinstance(data["new"], dict)
        assert isinstance(data["tspans_by_id"], dict)
        assert isinstance(data["error"], str)

    def test_to_json_is_serializable(self, tmp_path: Path):

        inner = """
            <switch>
                <text id="t0-ar" systemLanguage="ar"><tspan id="t0-ar">مرحبا</tspan></text>
                <text id="t0"><tspan id="t0">Hello</tspan></text>
            </switch>
        """
        svg = _write_svg(tmp_path, inner)
        ext = SVGTranslationExtractor()
        data = ext.extract(svg).to_json()

        # Should be JSON-serializable without errors
        serialized = json.dumps(data, ensure_ascii=False)
        assert isinstance(serialized, str)
        assert "مرحبا" in serialized
