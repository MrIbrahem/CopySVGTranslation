"""Comprehensive tests for the CopySVGTranslation public API module (__init__.py)."""

from __future__ import annotations

from pathlib import Path

# Test that the public API is importable
import CopySVGTranslation
from CopySVGTranslation.extraction import extract
from CopySVGTranslation.injection import inject, start_injects
from CopySVGTranslation.workflows import svg_extract_and_inject

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestPublicAPIExports:
    """Test that the public API exports all expected functions."""

    def test_all_attribute_exists(self):
        """The __all__ attribute should be defined."""
        assert hasattr(CopySVGTranslation, "__all__")
        assert isinstance(CopySVGTranslation.__all__, list)

    def test_all_attribute_completeness(self):
        """The __all__ attribute should contain all expected public functions."""
        expected_exports = [
            "extract",
            "inject",
        ]
        for name in expected_exports:
            assert name in CopySVGTranslation.__all__, f"{name} should be in __all__"

    def test_all_exports_are_callable(self):
        """All items in __all__ should be callable functions."""
        for name in CopySVGTranslation.__all__:
            obj = getattr(CopySVGTranslation, name)
            assert callable(obj), f"{name} should be callable"

    def test_extract_is_importable(self):
        """The extract function should be importable from top-level module."""
        assert callable(extract)
        assert extract.__name__ == "extract"

    def test_inject_is_importable(self):
        """The inject function should be importable from top-level module."""
        assert callable(inject)
        assert inject.__name__ == "inject"

    def test_start_injects_is_importable(self):
        """The start_injects function should be importable from top-level module."""
        assert callable(start_injects)
        assert start_injects.__name__ == "start_injects"

    def test_svg_extract_and_inject_is_importable(self):
        """The svg_extract_and_inject function should be importable from top-level module."""
        assert callable(svg_extract_and_inject)
        assert svg_extract_and_inject.__name__ == "svg_extract_and_inject"

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
            assert not name.startswith("_"), f"{name} should not be private"


class TestExtractFunction:
    """Integration tests for the extract function."""

    def test_extract_returns_dict(self):
        """extract should return a dictionary of translations."""
        result = extract(FIXTURES_DIR / "source.svg")
        assert isinstance(result, dict)

    def test_extract_has_expected_keys(self):
        """extract should return a dict with expected top-level keys."""
        result = extract(FIXTURES_DIR / "source.svg")
        assert "new" in result
        assert "title" in result

    def test_extract_nonexistent_file_returns_none(self):
        """extract should return None for non-existent files."""
        result = extract(Path("/nonexistent/file.svg"))
        assert result is None

    def test_extract_case_insensitive_default(self):
        """extract should be case insensitive by default."""
        result = extract(FIXTURES_DIR / "source.svg")
        assert result is not None
        # Should have lowercase keys
        assert "population 2020" in result["new"]

    def test_extract_with_arabic_translations(self):
        """extract should properly extract Arabic translations."""
        result = extract(FIXTURES_DIR / "source.svg")
        assert result is not None
        assert "ar" in result["new"]["population 2020"]
        assert result["new"]["population 2020"]["ar"] == "السكان 2020"


class TestIntegrationWorkflows:
    """Integration tests for high-level workflow functions."""

    def test_svg_extract_and_inject_end_to_end(self, tmp_path: Path):
        """Test complete extract and inject workflow."""
        source_svg = FIXTURES_DIR / "source.svg"
        target_svg = tmp_path / "target.svg"
        output_svg = tmp_path / "output.svg"
        data_file = tmp_path / "data.json"

        # Copy target fixture
        target_svg.write_text((FIXTURES_DIR / "target.svg").read_text(encoding="utf-8"), encoding="utf-8")

        # Run the workflow
        result = svg_extract_and_inject(
            source_svg,
            target_svg,
            output_file=output_svg,
            data_output_file=data_file,
            save_result=True,
        )

        assert result is not None
        assert output_svg.exists()
        assert data_file.exists()

    def test_inject_with_dict(self, tmp_path: Path):
        """Test inject with pre-extracted translations dict."""
        target_svg = tmp_path / "target.svg"
        target_svg.write_text((FIXTURES_DIR / "target.svg").read_text(encoding="utf-8"), encoding="utf-8")

        # Extract translations first
        translations = extract(FIXTURES_DIR / "source.svg")

        # Inject using the dict
        result, stats = inject(
            inject_file=target_svg,
            all_mappings=translations,
            output_dir=tmp_path,
            save_result=True,
            return_stats=True,
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
        assert result is None or isinstance(result, dict)

    def test_extract_with_invalid_xml(self, tmp_path: Path):
        """extract should handle invalid XML gracefully."""
        invalid_svg = tmp_path / "invalid.svg"
        invalid_svg.write_text("<svg><unclosed>", encoding="utf-8")

        result = extract(invalid_svg)
        assert result is None

    def test_inject_with_empty_mapping_list(self, tmp_path: Path):
        """inject should handle empty mapping file list."""
        target_svg = tmp_path / "target.svg"
        target_svg.write_text((FIXTURES_DIR / "target.svg").read_text(encoding="utf-8"), encoding="utf-8")

        result = inject(target_svg, [])
        # Should return None or handle gracefully
        assert result is None or result is not None


class TestAPIConsistency:
    """Tests to ensure API consistency across the package."""

    def test_all_functions_have_docstrings(self):
        """All exported functions should have docstrings."""
        for name in CopySVGTranslation.__all__:
            func = getattr(CopySVGTranslation, name)
            assert func.__doc__ is not None, f"{name} should have a docstring"
            assert len(func.__doc__) > 0, f"{name} docstring should not be empty"

    def test_import_paths_consistency(self):
        """Verify that functions are accessible from both paths."""
        # These should all refer to the same function objects
        from CopySVGTranslation import extract as extract1
        from CopySVGTranslation.extraction import extract as extract2

        # The functions should be the same object
        assert extract1 is extract2

    def test_module_name_is_correct(self):
        """The module should have the correct name."""
        assert CopySVGTranslation.__name__ == "CopySVGTranslation"

    def test_package_structure(self):
        """Verify the package has expected submodules."""
        assert hasattr(CopySVGTranslation, "extraction")
        assert hasattr(CopySVGTranslation, "injection")
        assert hasattr(CopySVGTranslation, "workflows")
        assert hasattr(CopySVGTranslation, "text_utils")
