"""
Unit tests for SVGTranslationService.
"""

from __future__ import annotations

from pathlib import Path

from CopySVGTranslation.config import TranslationConfig
from CopySVGTranslation.core.mapping import TranslationMapping
from CopySVGTranslation.result import InjectorData
from CopySVGTranslation.service import SVGTranslationService

SVG_NS = "http://www.w3.org/2000/svg"


def _wrap_svg(inner: str) -> str:
    return f'<svg xmlns="{SVG_NS}" version="1.1">{inner}</svg>'


def _write_svg(tmp_path: Path, inner: str, name: str = "test.svg") -> Path:
    p = tmp_path / name
    p.write_text(_wrap_svg(inner), encoding="utf-8")
    return p


class TestSVGTranslationService:
    def test_service_initialization(self):
        config = TranslationConfig(case_insensitive=False)
        service = SVGTranslationService(config)
        assert service.config.case_insensitive is False

    def test_extract_success(self, tmp_path: Path):
        inner = """
            <switch>
                <text id="t0-ar" systemLanguage="ar"><tspan id="t0-ar">مرحبا</tspan></text>
                <text id="t0"><tspan id="t0">Hello</tspan></text>
            </switch>
        """
        svg = _write_svg(tmp_path, inner)
        service = SVGTranslationService()
        result = service.extract(svg)

        assert result.success is True
        assert isinstance(result.data, TranslationMapping)
        assert "hello" in result.data.new

    def test_extract_file_not_found(self, tmp_path: Path):
        service = SVGTranslationService()
        result = service.extract(tmp_path / "missing.svg")

        assert result.success is False
        assert "not found" in result.error
        assert result.error_code == "io-error"

    def test_extract_invalid_xml(self, tmp_path: Path):
        svg = tmp_path / "invalid.svg"
        svg.write_text("<svg><invalid>", encoding="utf-8")
        service = SVGTranslationService()
        result = service.extract(svg)

        assert result.success is False
        assert result.error_code == "parse-error"

    def test_inject_success(self, tmp_path: Path):
        inner = """
            <switch>
                <text id="t0"><tspan id="t0">Hello</tspan></text>
            </switch>
        """
        svg = _write_svg(tmp_path, inner)
        service = SVGTranslationService()
        mapping = {"new": {"hello": {"ar": "مرحبا"}}}

        result = service.inject(svg, mapping)

        assert result.success is True
        assert isinstance(result.data, InjectorData)
        assert result.data.tree is not None
        assert result.stats.inserted_translations == 1

    def test_extract_and_inject(self, tmp_path: Path):
        src_inner = """
            <switch>
                <text id="t0-ar" systemLanguage="ar"><tspan id="t0-ar">مرحبا</tspan></text>
                <text id="t0"><tspan id="t0">Hello</tspan></text>
            </switch>
        """
        tgt_inner = """
            <switch>
                <text id="t0"><tspan id="t0">Hello</tspan></text>
            </switch>
        """
        src = _write_svg(tmp_path, src_inner, "src.svg")
        tgt = _write_svg(tmp_path, tgt_inner, "tgt.svg")

        service = SVGTranslationService()
        result = service.extract_and_inject(src, tgt)

        assert result.success is True
        assert result.stats.inserted_translations == 1

    def test_prepare_only(self, tmp_path: Path):
        inner = """
            <text id="t0">Hello</text>
        """
        svg = _write_svg(tmp_path, inner)
        service = SVGTranslationService()

        result = service.prepare_only(svg)

        assert result.success is True
        assert result.data is not None
        # Root text element should be inside a switch element now after preparation
        root = result.data.getroot()
        switch = root.find(f".//{{{SVG_NS}}}switch")
        assert switch is not None
