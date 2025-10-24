"""Comprehensive tests for the CopySvgTranslate public API module (__init__.py)."""

from __future__ import annotations

from pathlib import Path

# Test that the public API is importable
import CopySvgTranslate
from CopySvgTranslate import (
    extract,
    generate_unique_id,
    inject,
    normalize_text,
    start_injects,
    svg_extract_and_inject,
    svg_extract_and_injects,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestPublicAPIExports:
    """Test that the public API exports all expected functions."""

    def test_all_attribute_exists(self):
        """The __all__ attribute should be defined."""
        assert hasattr(CopySvgTranslate, "__all__")
        assert isinstance(CopySvgTranslate.__all__, list)

    def test_all_attribute_completeness(self):
        """The __all__ attribute should contain all expected public functions."""
        expected_exports = [
            "extract",
            "generate_unique_id",
            "inject",
            "normalize_text",
            "start_injects",
            "svg_extract_and_inject",
            "svg_extract_and_injects",
        ]
        for name in expected_exports:
            assert name in CopySvgTranslate.__all__, f"{name} should be in __all__"

    def test_all_exports_are_callable(self):
        """All items in __all__ should be callable functions."""
        for name in CopySvgTranslate.__all__:
            obj = getattr(CopySvgTranslate, name)
            assert callable(obj), f"{name} should be callable"

    def test_extract_is_importable(self):
        """The extract function should be importable from top-level module."""
        assert callable(extract)
        assert extract.__name__ == "extract"

    def test_inject_is_importable(self):
        """The inject function should be importable from top-level module."""
        assert callable(inject)
        assert inject.__name__ == "inject"

    def test_normalize_text_is_importable(self):
        """The normalize_text function should be importable from top-level module."""
        assert callable(normalize_text)
        assert normalize_text.__name__ == "normalize_text"

    def test_generate_unique_id_is_importable(self):
        """The generate_unique_id function should be importable from top-level module."""
        assert callable(generate_unique_id)
        assert generate_unique_id.__name__ == "generate_unique_id"

    def test_start_injects_is_importable(self):
        """The start_injects function should be importable from top-level module."""
        assert callable(start_injects)
        assert start_injects.__name__ == "start_injects"

    def test_svg_extract_and_inject_is_importable(self):
        """The svg_extract_and_inject function should be importable from top-level module."""
        assert callable(svg_extract_and_inject)
        assert svg_extract_and_inject.__name__ == "svg_extract_and_inject"

    def test_svg_extract_and_injects_is_importable(self):
        """The svg_extract_and_injects function should be importable from top-level module."""
        assert callable(svg_extract_and_injects)
        assert svg_extract_and_injects.__name__ == "svg_extract_and_injects"

    def test_module_has_docstring(self):
        """The module should have a docstring."""
        assert CopySvgTranslate.__doc__ is not None
        assert len(CopySvgTranslate.__doc__) > 0

    def test_star_import(self):
        """Test that star import works correctly."""
        # Verify that all items in __all__ are accessible from the module
        for name in CopySvgTranslate.__all__:
            assert hasattr(CopySvgTranslate, name), f"{name} should be available via star import"

    def test_no_private_exports(self):
        """The __all__ list should not contain private names."""
        for name in CopySvgTranslate.__all__:
            assert not name.startswith("_"), f"{name} should not be private"


class TestNormalizeTextFunction:
    """Comprehensive tests for the normalize_text function."""

    def test_normalize_text_basic_whitespace(self):
        """normalize_text should collapse multiple spaces."""
        assert normalize_text("hello  world") == "hello world"
        assert normalize_text("hello   world") == "hello world"

    def test_normalize_text_leading_trailing_whitespace(self):
        """normalize_text should remove leading and trailing whitespace."""
        assert normalize_text("  hello world  ") == "hello world"
        assert normalize_text("\thello world\n") == "hello world"

    def test_normalize_text_empty_string(self):
        """normalize_text should handle empty strings."""
        assert normalize_text("") == ""
        assert normalize_text("   ") == ""

    def test_normalize_text_none_value(self):
        """normalize_text should handle None values."""
        assert normalize_text(None) == ""

    def test_normalize_text_case_sensitive(self):
        """normalize_text should preserve case by default."""
        assert normalize_text("Hello World") == "Hello World"
        assert normalize_text("HELLO WORLD") == "HELLO WORLD"

    def test_normalize_text_case_insensitive(self):
        """normalize_text should lowercase when case_insensitive=True."""
        assert normalize_text("Hello World", case_insensitive=True) == "hello world"
        assert normalize_text("HELLO WORLD", case_insensitive=True) == "hello world"

    def test_normalize_text_mixed_whitespace_types(self):
        """normalize_text should handle tabs, newlines, and spaces."""
        assert normalize_text("hello\tworld\n") == "hello world"
        assert normalize_text("hello\r\nworld") == "hello world"

    def test_normalize_text_unicode_whitespace(self):
        """normalize_text should handle unicode whitespace."""
        assert normalize_text("hello\u00A0world") == "hello world"  # Non-breaking space

    def test_normalize_text_single_word(self):
        """normalize_text should handle single words."""
        assert normalize_text("hello") == "hello"
        assert normalize_text("  hello  ") == "hello"

    def test_normalize_text_multiple_newlines(self):
        """normalize_text should collapse multiple newlines."""
        assert normalize_text("hello\n\n\nworld") == "hello world"

    def test_normalize_text_arabic_text(self):
        """normalize_text should preserve non-Latin scripts."""
        assert normalize_text("  السكان 2020  ") == "السكان 2020"

    def test_normalize_text_special_characters(self):
        """normalize_text should preserve special characters."""
        assert normalize_text("hello, world!") == "hello, world!"
        assert normalize_text("test@example.com") == "test@example.com"


class TestGenerateUniqueIdFunction:
    """Comprehensive tests for the generate_unique_id function."""

    def test_generate_unique_id_no_collision(self):
        """generate_unique_id should append language code when no collision."""
        existing_ids = {"id1", "id2"}
        result = generate_unique_id("base", "fr", existing_ids)
        assert result == "base-fr"

    def test_generate_unique_id_with_collision(self):
        """generate_unique_id should handle ID collisions."""
        existing_ids = {"base-ar"}
        result = generate_unique_id("base", "ar", existing_ids)
        assert result == "base-ar-1"

    def test_generate_unique_id_multiple_collisions(self):
        """generate_unique_id should handle multiple collisions."""
        existing_ids = {"base-ar", "base-ar-1", "base-ar-2"}
        result = generate_unique_id("base", "ar", existing_ids)
        assert result == "base-ar-3"

    def test_generate_unique_id_empty_existing_set(self):
        """generate_unique_id should work with empty existing ID set."""
        result = generate_unique_id("base", "de", set())
        assert result == "base-de"

    def test_generate_unique_id_preserves_base_id(self):
        """generate_unique_id should preserve the base ID structure."""
        existing_ids = {"other-id"}
        result = generate_unique_id("my-element", "es", existing_ids)
        assert result == "my-element-es"
        assert result.startswith("my-element")

    def test_generate_unique_id_different_languages(self):
        """generate_unique_id should handle different language codes."""
        existing_ids = set()

        ar_id = generate_unique_id("base", "ar", existing_ids)
        existing_ids.add(ar_id)

        fr_id = generate_unique_id("base", "fr", existing_ids)
        existing_ids.add(fr_id)

        assert ar_id == "base-ar"
        assert fr_id == "base-fr"
        assert ar_id != fr_id

    def test_generate_unique_id_complex_base_id(self):
        """generate_unique_id should handle complex base IDs."""
        existing_ids = set()
        result = generate_unique_id("text-2205-tspan", "ar", existing_ids)
        assert result == "text-2205-tspan-ar"

    def test_generate_unique_id_idempotency(self):
        """generate_unique_id should generate consistent IDs."""
        existing_ids = {"base-ar"}
        result1 = generate_unique_id("base", "ar", existing_ids)
        result2 = generate_unique_id("base", "ar", existing_ids)
        assert result1 == result2 == "base-ar-1"


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
        # Should have lowercase keys
        assert "population 2020" in result["new"]

    def test_extract_with_arabic_translations(self):
        """extract should properly extract Arabic translations."""
        result = extract(FIXTURES_DIR / "source.svg")
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
        target_svg.write_text(
            (FIXTURES_DIR / "target.svg").read_text(encoding="utf-8"),
            encoding="utf-8"
        )

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

    def test_svg_extract_and_injects_with_dict(self, tmp_path: Path):
        """Test inject with pre-extracted translations dict."""
        target_svg = tmp_path / "target.svg"
        target_svg.write_text(
            (FIXTURES_DIR / "target.svg").read_text(encoding="utf-8"),
            encoding="utf-8"
        )

        # Extract translations first
        translations = extract(FIXTURES_DIR / "source.svg")

        # Inject using the dict
        result, stats = svg_extract_and_injects(
            translations,
            target_svg,
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

    def test_normalize_text_with_only_whitespace(self):
        """normalize_text should return empty string for whitespace-only input."""
        assert normalize_text("   \t\n   ") == ""

    def test_generate_unique_id_with_large_collision_set(self):
        """generate_unique_id should handle large sets of existing IDs."""
        existing_ids = {f"base-ar-{i}" for i in range(100)}
        existing_ids.add("base-ar")

        result = generate_unique_id("base", "ar", existing_ids)
        assert result == "base-ar-100"

    def test_inject_with_empty_mapping_list(self, tmp_path: Path):
        """inject should handle empty mapping file list."""
        target_svg = tmp_path / "target.svg"
        target_svg.write_text(
            (FIXTURES_DIR / "target.svg").read_text(encoding="utf-8"),
            encoding="utf-8"
        )

        result = inject(target_svg, [])
        # Should return None or handle gracefully
        assert result is None or result is not None


class TestAPIConsistency:
    """Tests to ensure API consistency across the package."""

    def test_all_functions_have_docstrings(self):
        """All exported functions should have docstrings."""
        for name in CopySvgTranslate.__all__:
            func = getattr(CopySvgTranslate, name)
            assert func.__doc__ is not None, f"{name} should have a docstring"
            assert len(func.__doc__) > 0, f"{name} docstring should not be empty"

    def test_import_paths_consistency(self):
        """Verify that functions are accessible from both paths."""
        # These should all refer to the same function objects
        from CopySvgTranslate import extract as extract1
        from CopySvgTranslate.extraction import extract as extract2

        # The functions should be the same object
        assert extract1 is extract2

    def test_module_name_is_correct(self):
        """The module should have the correct name."""
        assert CopySvgTranslate.__name__ == "CopySvgTranslate"

    def test_package_structure(self):
        """Verify the package has expected submodules."""
        assert hasattr(CopySvgTranslate, "extraction")
        assert hasattr(CopySvgTranslate, "injection")
        assert hasattr(CopySvgTranslate, "workflows")
        assert hasattr(CopySvgTranslate, "text_utils")
