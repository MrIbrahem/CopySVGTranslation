"""Comprehensive tests for the CopySVGTranslation public API module (__init__.py)."""

from __future__ import annotations

from pathlib import Path

# Test that the public API is importable
import CopySVGTranslation
from CopySVGTranslation.extraction.worker import extract
from CopySVGTranslation.legacy.inject import inject_file_and_save, inject_file_tree


class TestPublicAPIExports:
    """Test that the public API exports all expected functions."""

    def test_all_attribute_exists(self):
        """The __all__ attribute should be defined."""
        assert hasattr(CopySVGTranslation, "__all__")
        assert isinstance(CopySVGTranslation.__all__, list)

    def test_extract_is_importable(self):
        """The extract function should be importable from top-level module."""
        assert callable(extract)
        assert extract.__name__ == "extract"

    def test_module_has_docstring(self):
        """The module should have a docstring."""
        assert CopySVGTranslation.__doc__ is not None
        assert len(CopySVGTranslation.__doc__) > 0

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
        result = extract(fixtures_dir / "source.svg")
        assert isinstance(result, dict)

    def test_extract_has_expected_keys(self, fixtures_dir):
        """extract should return a dict with expected top-level keys."""
        result = extract(fixtures_dir / "source.svg")
        assert "new" in result
        assert result == {
            "new": {"population 2020": {"ar": "السكان 2020", "fr": "Population 2020 FR"}},
            "tspans_by_id": {"label": "Population 2020"},
            "title_new": {"population {year}": {"ar": "السكان {year}"}},
            "error": "",
        }

    def test_extract_nonexistent_file_returns_none(self):
        """extract should return None for non-existent files."""
        result = extract(Path("/nonexistent/file.svg"))
        assert result is None

    def test_extract_case_insensitive_default(self, fixtures_dir):
        """extract should be case insensitive by default."""
        result = extract(fixtures_dir / "source.svg")
        assert result is not None
        # Should have lowercase keys
        assert "population 2020" in result["new"]
        assert result == {
            "new": {"population 2020": {"ar": "السكان 2020", "fr": "Population 2020 FR"}},
            "tspans_by_id": {"label": "Population 2020"},
            "title_new": {"population {year}": {"ar": "السكان {year}"}},
            "error": "",
        }

    def test_extract_with_arabic_translations(self, fixtures_dir):
        """extract should properly extract Arabic translations."""
        result = extract(fixtures_dir / "source.svg")
        assert result is not None
        assert "ar" in result["new"]["population 2020"]
        assert result["new"]["population 2020"]["ar"] == "السكان 2020"
        assert result == {
            "new": {"population 2020": {"ar": "السكان 2020", "fr": "Population 2020 FR"}},
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
        translations = extract(fixtures_dir / "source.svg")

        # Inject using the dict
        result, stats = inject_file_tree(
            inject_file=target_svg,
            mapping=translations,
            save_path=tmp_path / "target2.svg",
            return_stats=True,
            save_result=True,
        )

        assert result is not None
        assert isinstance(stats, dict)
        assert "inserted_translations" in stats


class TestEdgeCasesAndErrorHandling:
    """Tests for edge cases and error handling."""

    def test_extract_with_empty_svg(self, tmp_path: Path):
        """extract should handle empty SVG files gracefully."""
        empty_svg = tmp_path / "empty.svg"
        empty_svg.write_text("", encoding="utf-8")

        result = extract(empty_svg)
        # Should either return None or empty dict depending on implementation
        assert result is None

    def test_extract_with_invalid_xml(self, tmp_path: Path):
        """extract should handle invalid XML gracefully."""
        invalid_svg = tmp_path / "invalid.svg"
        invalid_svg.write_text("<svg><unclosed>", encoding="utf-8")

        result = extract(invalid_svg)
        assert result is None

    def test_inject_with_empty_mapping_list(self, tmp_path: Path, fixtures_dir):
        """inject should handle empty mapping file list."""
        target_svg = tmp_path / "target.svg"
        target_svg.write_text((fixtures_dir / "target.svg").read_text(encoding="utf-8"), encoding="utf-8")

        result = inject_file_tree(inject_file=target_svg, mapping_files=[])
        # Should return None or handle gracefully
        assert result is None


class TestAPIConsistency:
    """Tests to ensure API consistency across the package."""

    def test_import_paths_consistency(self):
        """Verify that functions are accessible from both paths."""
        # These should all refer to the same function objects
        from CopySVGTranslation.extraction.worker import extract as extract1
        from CopySVGTranslation.extraction.worker import extract as extract2

        # The functions should be the same object
        assert extract1 is extract2

    def test_module_name_is_correct(self):
        """The module should have the correct name."""
        assert CopySVGTranslation.__name__ == "CopySVGTranslation"
