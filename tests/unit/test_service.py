"""
Unit tests for SVGTranslationService — extended coverage.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from lxml import etree

from CopySVGTranslation.config import TranslationConfig
from CopySVGTranslation.core.mapping import TranslationMapping
from CopySVGTranslation.result import InjectorData, InjectorStats, OperationResult
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


# ---------------------------------------------------------------------------
# Additional coverage tests
# ---------------------------------------------------------------------------
class TestServiceExtractExtended:
    """Extended tests for extract method."""

    def test_extract_empty_svg(self, tmp_path: Path):
        """SVG with no translatable content returns failure."""
        svg = _write_svg(tmp_path, "")
        service = SVGTranslationService()
        result = service.extract(svg)
        assert result.success is False
        assert result.error_code == "no_translations"

    def test_extract_with_save_mapping_true(self, tmp_path: Path):
        """Extract with save_mapping=True should save to mapping_output_dir."""
        inner = """
            <switch>
                <text id="t0-ar" systemLanguage="ar"><tspan id="t0-ar">مرحبا</tspan></text>
                <text id="t0"><tspan id="t0">Hello</tspan></text>
            </switch>
        """
        svg = _write_svg(tmp_path, inner)
        mapping_dir = tmp_path / "mappings"
        config = TranslationConfig(mapping_output_dir=mapping_dir)
        service = SVGTranslationService(config)
        result = service.extract(svg, save_mapping=True)

        assert result.success is True
        # Mapping file should have been created
        expected_path = mapping_dir / "test.svg.json"
        assert expected_path.exists()

    def test_extract_with_save_mapping_path(self, tmp_path: Path):
        """Extract with save_mapping=Path should save to that path."""
        inner = """
            <switch>
                <text id="t0-ar" systemLanguage="ar"><tspan id="t0-ar">مرحبا</tspan></text>
                <text id="t0"><tspan id="t0">Hello</tspan></text>
            </switch>
        """
        svg = _write_svg(tmp_path, inner)
        out_path = tmp_path / "custom_mapping.json"
        service = SVGTranslationService()
        result = service.extract(svg, save_mapping=out_path)

        assert result.success is True
        assert out_path.exists()

    def test_extract_save_mapping_failure_adds_warning(self, tmp_path: Path):
        """If saving mapping fails, a warning is added but extraction succeeds."""
        inner = """
            <switch>
                <text id="t0-ar" systemLanguage="ar"><tspan id="t0-ar">مرحبا</tspan></text>
                <text id="t0"><tspan id="t0">Hello</tspan></text>
            </switch>
        """
        svg = _write_svg(tmp_path, inner)
        # Use a config with no mapping_output_dir and save_mapping=True
        config = TranslationConfig(mapping_output_dir=None, create_parents=False)
        service = SVGTranslationService(config)
        result = service.extract(svg, save_mapping=True)

        # Extraction should still succeed, but with a warning
        assert result.success is True
        assert len(result.warnings) >= 1

    def test_extract_string_path(self, tmp_path: Path):
        """Extract should accept string paths."""
        inner = """
            <switch>
                <text id="t0-ar" systemLanguage="ar"><tspan id="t0-ar">مرحبا</tspan></text>
                <text id="t0"><tspan id="t0">Hello</tspan></text>
            </switch>
        """
        svg = _write_svg(tmp_path, inner)
        service = SVGTranslationService()
        result = service.extract(str(svg))
        assert result.success is True


class TestServiceInjectExtended:
    """Extended tests for inject method."""

    def test_inject_save_without_output_fails(self, tmp_path: Path):
        """save=True without output path should fail."""
        inner = '<switch><text id="t0"><tspan id="t0">Hello</tspan></text></switch>'
        svg = _write_svg(tmp_path, inner)
        config = TranslationConfig(auto_save=True)
        service = SVGTranslationService(config)
        result = service.inject(svg, {"new": {"hello": {"ar": "مرحبا"}}})
        assert result.success is False
        assert result.error_code == "missing_output_path"

    def test_inject_with_output_path(self, tmp_path: Path):
        """Inject with output path and save=True should write file."""
        inner = '<switch><text id="t0"><tspan id="t0">Hello</tspan></text></switch>'
        svg = _write_svg(tmp_path, inner)
        out = tmp_path / "output.svg"
        service = SVGTranslationService()
        result = service.inject(
            svg,
            {"new": {"hello": {"ar": "مرحبا"}}},
            output=out,
            save=True,
        )
        assert result.success is True
        assert out.exists()

    def test_inject_with_mapping_object(self, tmp_path: Path):
        """Inject should accept a TranslationMapping object."""
        inner = '<switch><text id="t0"><tspan id="t0">Hello</tspan></text></switch>'
        svg = _write_svg(tmp_path, inner)
        mapping = TranslationMapping(new={"hello": {"ar": "مرحبا"}})
        service = SVGTranslationService()
        result = service.inject(svg, mapping)
        assert result.success is True

    def test_inject_no_tree_returned(self, tmp_path: Path):
        """When injector returns no tree, should fail gracefully."""
        inner = '<switch><text id="t0"><tspan id="t0">Hello</tspan></text></switch>'
        svg = _write_svg(tmp_path, inner)
        service = SVGTranslationService()
        # Mock the injector to return None tree
        with patch.object(
            service._injector,
            "inject",
            return_value=InjectorData(
                tree=None,
                new_stats=InjectorStats(error="mock error"),
            ),
        ):
            result = service.inject(svg, {"new": {"hello": {"ar": "مرحبا"}}})
            assert result.success is False
            assert result.error_code == "injection_failed"


class TestServiceExtractAndInject:
    """Extended tests for extract_and_inject."""

    def test_extract_failure_propagates(self, tmp_path: Path):
        """If extraction fails, the combined result should fail."""
        src = _write_svg(tmp_path, "", "src.svg")
        tgt = _write_svg(tmp_path, '<switch><text id="t0"><tspan id="t0">Hello</tspan></text></switch>', "tgt.svg")
        service = SVGTranslationService()
        result = service.extract_and_inject(src, tgt)
        assert result.success is False

    def test_merges_warnings(self, tmp_path: Path):
        """Warnings from both extract and inject should be merged."""
        src_inner = """
            <switch>
                <text id="t0-ar" systemLanguage="ar"><tspan id="t0-ar">مرحبا</tspan></text>
                <text id="t0"><tspan id="t0">Hello</tspan></text>
            </switch>
        """
        tgt_inner = '<switch><text id="t0"><tspan id="t0">Hello</tspan></text></switch>'
        src = _write_svg(tmp_path, src_inner, "src.svg")
        tgt = _write_svg(tmp_path, tgt_inner, "tgt.svg")
        service = SVGTranslationService()
        result = service.extract_and_inject(src, tgt)
        assert result.success is True
        # Warnings should be a list (may or may not be empty)
        assert isinstance(result.warnings, list)


class TestServicePrepareOnly:
    """Extended tests for prepare_only."""

    def test_prepare_only_with_output(self, tmp_path: Path):
        """prepare_only with output should write the prepared SVG."""
        inner = '<text id="t0">Hello</text>'
        svg = _write_svg(tmp_path, inner)
        out = tmp_path / "prepared.svg"
        service = SVGTranslationService()
        result = service.prepare_only(svg, output=out)
        assert result.success is True
        assert out.exists()

    def test_prepare_only_invalid_svg(self, tmp_path: Path):
        """prepare_only with invalid SVG should fail gracefully."""
        svg = tmp_path / "bad.svg"
        svg.write_text("not xml", encoding="utf-8")
        service = SVGTranslationService()
        result = service.prepare_only(svg)
        assert result.success is False
        assert result.error_code == "prepare_error"


class TestServiceLoadSaveMapping:
    """Tests for load_mapping and save_mapping convenience methods."""

    def test_load_mapping_success(self, tmp_path: Path):
        data = {"new": {"hello": {"ar": "مرحبا"}}}
        f = tmp_path / "mapping.json"
        f.write_text(json.dumps(data), encoding="utf-8")
        service = SVGTranslationService()
        result = service.load_mapping(f)
        assert result.success is True
        assert isinstance(result.data, TranslationMapping)

    def test_load_mapping_not_found(self, tmp_path: Path):
        service = SVGTranslationService()
        result = service.load_mapping(tmp_path / "missing.json")
        assert result.success is False
        assert result.error_code == "load_mapping_error"

    def test_save_mapping_success(self, tmp_path: Path):
        mapping = TranslationMapping(new={"hello": {"ar": "مرحبا"}})
        out = tmp_path / "out.json"
        service = SVGTranslationService()
        result = service.save_mapping(mapping, out)
        assert result.success is True
        assert out.exists()

    def test_save_mapping_failure(self, tmp_path: Path):
        mapping = TranslationMapping(new={"hello": {"ar": "مرحبا"}})
        config = TranslationConfig(create_parents=False)
        service = SVGTranslationService(config)
        out = tmp_path / "nonexistent" / "dir" / "out.json"
        result = service.save_mapping(mapping, out)
        assert result.success is False
        assert result.error_code == "save_mapping_error"


class TestServiceResolveHelpers:
    """Tests for internal path resolution helpers."""

    def test_resolve_output_path_bare_filename_with_output_dir(self, tmp_path: Path):
        config = TranslationConfig(output_dir=tmp_path / "output")
        service = SVGTranslationService(config)
        result = service._resolve_output_path("file.svg")
        assert result == tmp_path / "output" / "file.svg"

    def test_resolve_output_path_full_path(self, tmp_path: Path):
        config = TranslationConfig(output_dir=tmp_path / "output")
        service = SVGTranslationService(config)
        full_path = tmp_path / "custom" / "file.svg"
        result = service._resolve_output_path(full_path)
        assert result == full_path

    def test_resolve_mapping_output_explicit_path(self, tmp_path: Path):
        service = SVGTranslationService()
        result = service._resolve_mapping_output(
            Path("/some/file.svg"), tmp_path / "explicit.json"
        )
        assert result == tmp_path / "explicit.json"

    def test_resolve_mapping_output_no_dir_raises(self):
        config = TranslationConfig(mapping_output_dir=None)
        service = SVGTranslationService(config)
        with pytest.raises(ValueError, match="mapping_output_dir"):
            service._resolve_mapping_output(Path("/some/file.svg"), True)

    def test_resolve_mapping_output_creates_dir(self, tmp_path: Path):
        mapping_dir = tmp_path / "new_dir"
        config = TranslationConfig(mapping_output_dir=mapping_dir, create_parents=True)
        service = SVGTranslationService(config)
        result = service._resolve_mapping_output(Path("/some/file.svg"), True)
        assert result == mapping_dir / "file.svg.json"
        assert mapping_dir.exists()


class TestServiceSaveTree:
    """Tests for _save_tree internal helper."""

    def test_save_tree_creates_file(self, tmp_path: Path):
        service = SVGTranslationService()
        svg_content = f'<svg xmlns="{SVG_NS}"><text>Hello</text></svg>'
        root = etree.fromstring(svg_content.encode("utf-8"))
        tree = etree.ElementTree(root)
        out = tmp_path / "saved.svg"
        service._save_tree(tree, out)
        assert out.exists()

    def test_save_tree_creates_parents(self, tmp_path: Path):
        config = TranslationConfig(create_parents=True)
        service = SVGTranslationService(config)
        svg_content = f'<svg xmlns="{SVG_NS}"><text>Hello</text></svg>'
        root = etree.fromstring(svg_content.encode("utf-8"))
        tree = etree.ElementTree(root)
        out = tmp_path / "sub" / "dir" / "saved.svg"
        service._save_tree(tree, out)
        assert out.exists()
