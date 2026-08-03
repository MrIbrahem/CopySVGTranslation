#

"""
Comprehensive pytest tests for CopySVGTranslation covering edge cases and additional functionality.
"""

import json
from pathlib import Path

import pytest
from lxml import etree

from CopySVGTranslation.injection import (
    SvgStructureExceptionError,
    inject_file_and_save,
    inject_file_tree,
    make_translation_ready,
)
from CopySVGTranslation.utils import (
    generate_unique_id,
    load_all_mappings,
)

# -------------------------------
# Preparation tests
# -------------------------------


class TestPreparation:
    """Test cases for SVG preparation functions."""

    def test_svg_structure_exception(self):
        """Test SvgStructureExceptionError creation."""
        exc = SvgStructureExceptionError("test-code", extra="Extra info")
        assert exc.code == "test-code"
        assert exc.extra == "Extra info"
        assert "test-code" in str(exc)
        assert "Extra info" in str(exc)

    def test_make_translation_ready_nonexistent_file(self):
        """Test make_translation_ready with nonexistent file."""
        with pytest.raises(FileNotFoundError):
            make_translation_ready(Path("/nonexistent/file.svg"))

    def test_make_translation_ready_with_valid_svg(self, temp_dir):
        """Test make_translation_ready with valid SVG."""
        svg_path = temp_dir / "test.svg"
        svg_content = """<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><switch><text id="t1"><tspan>Hello</tspan></text></switch></svg>"""
        svg_path.write_text(svg_content, encoding="utf-8")
        tree, root = make_translation_ready(svg_path)
        assert tree is not None
        assert root is not None


# -------------------------------
# Injector tests
# -------------------------------


class TestInjector:
    """Test cases for injection functions."""

    def test_load_all_mappings_single_file(self, temp_dir):
        """Test loading a single mapping file."""
        mapping_file = temp_dir / "mapping.json"
        test_mapping = {"new": {"hello": {"ar": "مرحبا"}}}
        mapping_file.write_text(json.dumps(test_mapping, ensure_ascii=False), encoding="utf-8")
        result = load_all_mappings([mapping_file])
        assert "new" in result
        assert result["new"]["hello"]["ar"] == "مرحبا"

        assert result == {"new": {"hello": {"ar": "مرحبا"}}}

    def test_load_all_mappings_multiple_files(self, temp_dir):
        """Test loading multiple mapping files."""
        m1 = temp_dir / "m1.json"
        m2 = temp_dir / "m2.json"
        m1.write_text(json.dumps({"key1": {"value": 1}}), encoding="utf-8")
        m2.write_text(json.dumps({"key2": {"value": 2}}), encoding="utf-8")
        result = load_all_mappings([m1, m2])
        assert "key1" in result
        assert "key2" in result

        assert result == {"key1": {"value": 1}, "key2": {"value": 2}}

    def test_load_all_mappings_nonexistent_file(self, temp_dir):
        """Test loading with nonexistent file."""
        result = load_all_mappings([temp_dir / "nonexistent.json"])
        assert result == {}

    def test_load_all_mappings_invalid_json(self, temp_dir):
        """Test loading with invalid JSON."""
        invalid_file = temp_dir / "invalid.json"
        invalid_file.write_text("{ invalid json", encoding="utf-8")
        result = load_all_mappings([invalid_file])
        assert result == {}

    def test_load_all_mappings_merge_behavior(self, temp_dir):
        """Test that mappings are merged correctly."""
        m1 = temp_dir / "m1.json"
        m2 = temp_dir / "m2.json"
        m1.write_text(json.dumps({"key": {"lang1": "value1"}}), encoding="utf-8")
        m2.write_text(json.dumps({"key": {"lang2": "value2"}}), encoding="utf-8")
        result = load_all_mappings([m1, m2])
        assert "lang1" in result["key"]
        assert "lang2" in result["key"]

    def test_generate_unique_id_empty_base(self):
        """Test unique ID generation with empty base ID."""
        result = generate_unique_id("", "ar", set())
        assert result == "-ar"

    def test_generate_unique_id_with_special_characters(self):
        """Test unique ID generation with special characters in base."""
        result = generate_unique_id("text-123", "fr", set())
        assert result == "text-123-fr"

    def test_inject_with_all_mappings_parameter(self, temp_dir):
        """Test inject using all_mappings parameter."""
        svg_path = temp_dir / "test.svg"
        svg_content = """<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><switch><text id="text1"><tspan>Hello</tspan></text></switch></svg>"""
        svg_path.write_text(svg_content, encoding="utf-8")
        mappings = {"new": {"hello": {"ar": "مرحبا"}}}
        tree, stats = inject_file_tree(
            inject_file=svg_path,
            all_mappings=mappings,
            return_stats=True,
        )
        assert tree is not None
        assert stats is not None

    def test_inject_with_output_dir(self, temp_dir):
        """Test inject with output_dir parameter."""
        svg_path = temp_dir / "test.svg"
        out_dir = temp_dir / "out"
        out_dir.mkdir()
        svg_content = """<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><switch><text id="t"><tspan>Hello</tspan></text></switch></svg>"""
        svg_path.write_text(svg_content, encoding="utf-8")
        mappings = {"new": {"hello": {"ar": "مرحبا"}}}
        tree = inject_file_and_save(
            inject_file=svg_path,
            all_mappings=mappings,
            save_path=out_dir / "test.svg",
        )
        assert tree is not None
        assert (out_dir / "test.svg").exists()

    def test_inject_case_sensitive(self, temp_dir):
        """Test inject with case_insensitive=False."""
        svg_path = temp_dir / "test.svg"
        svg_content = """<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><switch><text id="t"><tspan>Hello</tspan></text></switch></svg>"""
        svg_path.write_text(svg_content, encoding="utf-8")
        mappings = {"new": {"Hello": {"ar": "مرحبا"}}}
        tree, stats = inject_file_tree(
            inject_file=svg_path,
            all_mappings=mappings,
            case_insensitive=False,
            return_stats=True,
        )
        assert tree is not None
        assert stats["inserted_translations"] == 1

        assert stats == {
            "all_languages": 1,
            "new_languages": 1,
            "processed_switches": 1,
            "inserted_translations": 1,
            "skipped_translations": 0,
            "updated_translations": 0,
            "languages_before": [],
            "languages_after": ["ar"],
            "error": "",
        }


# -------------------------------
# Edge case tests
# -------------------------------


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_generate_unique_id_with_many_collisions(self):
        """Test unique ID generation with many existing IDs."""
        existing = {f"id-ar-{i}" for i in range(100)}
        existing.add("id-ar")
        result = generate_unique_id("id", "ar", existing)
        assert result == "id-ar-100"

    def test_inject_with_empty_mappings(self, temp_dir):
        """Test injection with empty mappings."""
        svg = temp_dir / "test.svg"
        svg.write_text(
            '<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><text>Test</text></svg>', encoding="utf-8"
        )
        result = inject_file_tree(
            inject_file=svg,
            all_mappings={},
        )
        assert result is None

    def test_inject_return_stats_false(self, temp_dir):
        """Test inject with return_stats=False."""
        svg = temp_dir / "test.svg"
        svg.write_text(
            '<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><switch><text id="t"><tspan>Hello</tspan></text></switch></svg>',
            encoding="utf-8",
        )
        mappings = {"new": {"hello": {"ar": "مرحبا"}}}
        result = inject_file_tree(
            inject_file=svg,
            all_mappings=mappings,
            return_stats=False,
        )
        assert result is not None
        assert isinstance(result, etree._ElementTree)
