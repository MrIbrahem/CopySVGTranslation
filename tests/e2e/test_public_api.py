"""End-to-end tests for the supported public API."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

import CopySVGTranslation
from CopySVGTranslation import SVGTranslationService


class TestPublicAPIExports:
    """Verify that only the supported public API is exported."""

    def test_all_exports_are_available(self) -> None:
        expected_exports = {
            "__version__",
            "CopySVGTranslationError",
            "NestedTspanDetector",
            "NestedTspanFlattener",
            "NestedStructureService",
            "RepairResult",
            "SVGTranslationService",
            "TranslationConfig",
            "TranslationEntry",
            "TranslationMapping",
        }

        assert set(CopySVGTranslation.__all__) == expected_exports
        for name in CopySVGTranslation.__all__:
            assert hasattr(CopySVGTranslation, name)

    def test_module_has_documented_public_facade(self) -> None:
        assert CopySVGTranslation.__doc__
        assert CopySVGTranslation.__name__ == "CopySVGTranslation"
        assert SVGTranslationService is CopySVGTranslation.SVGTranslationService

    @pytest.mark.parametrize(
        "name",
        ["SVGTranslationExtractor", "SVGTranslationInjector"],
    )
    def test_low_level_components_are_not_top_level_exports(self, name: str) -> None:
        assert name not in CopySVGTranslation.__all__
        assert not hasattr(CopySVGTranslation, name)

    @pytest.mark.parametrize(
        ("module_name", "name"),
        [
            ("CopySVGTranslation.extraction", "SVGTranslationExtractor"),
            ("CopySVGTranslation.injection", "SVGTranslationInjector"),
        ],
    )
    def test_low_level_components_are_not_subpackage_exports(self, module_name: str, name: str) -> None:
        module = importlib.import_module(module_name)

        assert name not in module.__all__
        assert not hasattr(module, name)

    def test_legacy_package_is_not_importable(self) -> None:
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module("CopySVGTranslation.legacy")


class TestServiceWorkflows:
    """Exercise extraction and injection through the supported service facade."""

    def test_extract_returns_a_mapping(self, fixtures_dir: Path) -> None:
        result = SVGTranslationService().extract(fixtures_dir / "source.svg")

        assert result.success
        assert result.data is not None
        assert result.data.to_json() == {
            "new": {"population 2020": {"ar": "السكان 2020", "fr": "Population 2020 FR"}},
            "meta": {},
            "tspans_by_id": {"label": "Population 2020"},
            "title_new": {"population {year}": {"ar": "السكان {year}"}},
            "error": "",
        }

    def test_extract_reports_a_missing_file_as_a_failed_result(self, tmp_path: Path) -> None:
        result = SVGTranslationService().extract(tmp_path / "does-not-exist.svg")

        assert not result.success
        assert result.data is None
        assert result.error

    def test_extract_and_inject_saves_the_translated_svg(self, fixtures_dir: Path, tmp_path: Path) -> None:
        service = SVGTranslationService()
        extraction = service.extract(fixtures_dir / "source.svg")
        assert extraction.success
        assert extraction.data is not None

        input_svg = tmp_path / "input.svg"
        output_svg = tmp_path / "translated.svg"
        input_svg.write_text((fixtures_dir / "target.svg").read_text(encoding="utf-8"), encoding="utf-8")

        injection = service.inject(
            input_svg,
            extraction.data,
            output=output_svg,
            save=True,
        )

        assert injection.success
        assert injection.data is not None
        assert injection.stats is not None
        assert injection.stats.inserted_translations > 0
        assert output_svg.exists()
        assert 'systemLanguage="ar"' in output_svg.read_text(encoding="utf-8")
