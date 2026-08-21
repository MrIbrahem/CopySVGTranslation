"""Comprehensive tests for the CopySVGTranslation public API module (__init__.py)."""

from __future__ import annotations

from pathlib import Path

# Test that the public API is importable
import CopySVGTranslation
from CopySVGTranslation import SVGTranslationService


class TestPublicAPIExports:
    """Test that the public API exports all expected functions."""

    def test_all_attribute_exists(self):
        """The __all__ attribute should be defined."""
        assert hasattr(CopySVGTranslation, "__all__")
        assert isinstance(CopySVGTranslation.__all__, list)

    def test_module_has_docstring(self):
        """The module should have a docstring."""
        assert CopySVGTranslation.__doc__ is not None
        assert len(CopySVGTranslation.__doc__) > 0

    def test_service_is_importable(self):
        """SVGTranslationService should be importable from the public API."""
        from CopySVGTranslation import SVGTranslationService

        assert callable(SVGTranslationService)
        assert SVGTranslationService.__name__ == "SVGTranslationService"

    def test_star_import(self):
        """Test that star import works correctly."""
        # Verify that all items in __all__ are accessible from the module
        for name in CopySVGTranslation.__all__:
            assert hasattr(CopySVGTranslation, name), f"{name} should be available via star import"

    def test_no_private_exports(self):
        """The __all__ list should not contain private names."""
        for name in CopySVGTranslation.__all__:
            if name != "__version__":
                assert not name.startswith("_"), f"{name} should not be private"


class TestExtractFunction:
    """Integration tests for the extract function."""

    def test_extract_returns_dict(self, fixtures_dir):
        """extract should return a dictionary of translations."""
        service = SVGTranslationService()
        _result = service.extract(fixtures_dir / "source.svg")
        assert _result.success
        assert _result.data is not None
        result = _result.data.to_json()
        assert isinstance(result, dict)

    def test_extract_has_expected_keys(self, fixtures_dir):
        """extract should return a dict with expected top-level keys."""
        service = SVGTranslationService()
        _result = service.extract(fixtures_dir / "source.svg")
        assert _result.success
        assert _result.data is not None
        result = _result.data.to_json()
        assert "new" in result
        assert result == {
            "new": {"population 2020": {"ar": "السكان 2020", "fr": "Population 2020 FR"}},
            "meta": {},
            "tspans_by_id": {"label": "Population 2020"},
            "title_new": {"population {year}": {"ar": "السكان {year}"}},
            "error": "",
        }

    def test_extract_nonexistent_file_returns_none(self):
        """extract should return failed result for non-existent files."""
        service = SVGTranslationService()
        result = service.extract(Path("/nonexistent/file.svg"))
        assert not result.success
        assert result.data is None

    def test_extract_case_insensitive_default(self, fixtures_dir):
        """extract should be case insensitive by default."""
        service = SVGTranslationService()
        _result = service.extract(fixtures_dir / "source.svg")
        assert _result.success
        assert _result.data is not None
        result = _result.data.to_json()
        assert result is not None
        # Should have lowercase keys
        assert "population 2020" in result["new"]
        assert result == {
            "new": {"population 2020": {"ar": "السكان 2020", "fr": "Population 2020 FR"}},
            "meta": {},
            "tspans_by_id": {"label": "Population 2020"},
            "title_new": {"population {year}": {"ar": "السكان {year}"}},
            "error": "",
        }

    def test_extract_with_arabic_translations(self, fixtures_dir):
        """extract should properly extract Arabic translations."""
        service = SVGTranslationService()
        _result = service.extract(fixtures_dir / "source.svg")
        assert _result.success
        assert _result.data is not None
        result = _result.data.to_json()
        assert result is not None
        assert "ar" in result["new"]["population 2020"]
        assert result["new"]["population 2020"]["ar"] == "السكان 2020"
        assert result == {
            "new": {"population 2020": {"ar": "السكان 2020", "fr": "Population 2020 FR"}},
            "meta": {},
            "tspans_by_id": {"label": "Population 2020"},
            "title_new": {"population {year}": {"ar": "السكان {year}"}},
            "error": "",
        }


class TestIntegrationWorkflows:
    """Integration tests for high-level workflow functions."""

    def test_inject_with_dict(self, tmp_path: Path, fixtures_dir):
        """Test inject with pre-extracted translations dict."""
        target_svg = tmp_path / "target.svg"
        target_svg.write_text((fixtures_dir / "target.svg").read_text(encoding="utf-8"), encoding="utf-8")

        # Extract translations first
        service = SVGTranslationService()
        _extract_result = service.extract(fixtures_dir / "source.svg")
        assert _extract_result.success

        # Inject using the TranslationMapping via the public service API
        result = service.inject(
            svg_path=target_svg,
            mapping=_extract_result.data,
            output=tmp_path / "target2.svg",
            save=True,
        )

        assert result.success
        stats = result.data.inject_stats.to_json()
        assert isinstance(stats, dict)
        assert "inserted_translations" in stats


class TestEdgeCasesAndErrorHandling:
    """Tests for edge cases and error handling."""

    def test_extract_with_empty_svg(self, tmp_path: Path):
        """extract should handle empty SVG files gracefully."""
        empty_svg = tmp_path / "empty.svg"
        empty_svg.write_text("", encoding="utf-8")

        service = SVGTranslationService()
        result = service.extract(empty_svg)
        # Should return a failed result
        assert not result.success
        assert result.data is None

    def test_extract_with_invalid_xml(self, tmp_path: Path):
        """extract should handle invalid XML gracefully."""
        invalid_svg = tmp_path / "invalid.svg"
        invalid_svg.write_text("<svg><unclosed>", encoding="utf-8")

        service = SVGTranslationService()
        result = service.extract(invalid_svg)
        assert not result.success
        assert result.data is None

    def test_inject_with_none_mapping_raises(self, tmp_path: Path, fixtures_dir):
        """inject should return a failed result when mapping is None."""
        target_svg = tmp_path / "target.svg"
        target_svg.write_text((fixtures_dir / "target.svg").read_text(encoding="utf-8"), encoding="utf-8")

        service = SVGTranslationService()
        result = service.inject(svg_path=target_svg, mapping=None)
        assert not result.success
        assert result.error is not None


class TestAPIConsistency:
    """Tests to ensure API consistency across the package."""

    def test_import_paths_consistency(self):
        """Verify that functions are accessible from both paths."""
        # These should all refer to the same function objects
        from CopySVGTranslation import SVGTranslationService as Svc1
        from CopySVGTranslation import SVGTranslationService as Svc2

        # The class should be the same object
        assert Svc1 is Svc2

    def test_module_name_is_correct(self):
        """The module should have the correct name."""
        assert CopySVGTranslation.__name__ == "CopySVGTranslation"
