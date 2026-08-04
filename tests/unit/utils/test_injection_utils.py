"""
Unit tests for CopySVGTranslation/injection/utils.py module.
"""

import json
import shutil
import tempfile
from pathlib import Path

import pytest

from CopySVGTranslation.utils.injection_utils import (
    generate_unique_id,
    load_all_mappings,
)


class TestSetup:
    @pytest.fixture(autouse=True)
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.svg_path = self.test_dir / "source.svg"
        self.svg_path.write_text("<svg></svg>", encoding="utf-8")

        yield
        """Clean up test fixtures."""
        # Clean up temporary files
        shutil.rmtree(self.test_dir)


class TestLoadAllMappingsEdgeCases(TestSetup):
    """Test suite for load_all_mappings edge cases."""

    def test_load_all_mappings_empty_list(self):
        """Test loading with empty file list."""
        result = load_all_mappings([])

        assert result == {}

    def test_load_all_mappings_empty_json_file(self):
        """Test loading empty JSON file."""
        mapping_file = self.test_dir / "empty.json"
        mapping_file.write_text("{}", encoding="utf-8")

        result = load_all_mappings([mapping_file])

        assert result == {}

    def test_load_all_mappings_corrupted_json(self):
        """Test loading corrupted JSON file."""
        mapping_file = self.test_dir / "corrupted.json"
        mapping_file.write_text("{ corrupted", encoding="utf-8")

        result = load_all_mappings([mapping_file])

        assert result == {}

    def test_load_all_mappings_nested_structure(self):
        """Test loading with nested mapping structure."""
        mapping_file = self.test_dir / "nested.json"
        test_mapping = {
            "new": {"hello": {"ar": "مرحبا", "fr": "Bonjour"}},
            "title": {"Population ": {"ar": "السكان ", "fr": "Population "}},
        }
        with open(mapping_file, "w", encoding="utf-8") as f:
            json.dump(test_mapping, f, ensure_ascii=False)

        result = load_all_mappings([mapping_file])

        assert "new" in result
        assert "title" in result

        assert result == {
            "new": {"hello": {"ar": "مرحبا", "fr": "Bonjour"}},
            "title": {"Population ": {"ar": "السكان ", "fr": "Population "}},
        }

    def test_load_all_mappings_merge_overlapping_keys(self):
        """Test merging mappings with overlapping keys."""
        m1 = self.test_dir / "m1.json"
        m2 = self.test_dir / "m2.json"

        with open(m1, "w", encoding="utf-8") as f:
            json.dump({"key": {"lang1": "value1"}}, f)

        with open(m2, "w", encoding="utf-8") as f:
            json.dump({"key": {"lang2": "value2"}}, f)

        result = load_all_mappings([m1, m2])

        assert "lang1" in result["key"]
        assert "lang2" in result["key"]

        assert result == {"key": {"lang1": "value1", "lang2": "value2"}}

    def test_load_all_mappings_string_paths(self):
        """Test loading with string paths instead of Path objects."""
        mapping_file = self.test_dir / "test.json"
        with open(mapping_file, "w", encoding="utf-8") as f:
            json.dump({"key": {"value": "test"}}, f)

        result = load_all_mappings([str(mapping_file)])

        assert "key" in result

        assert result == {"key": {"value": "test"}}


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

    def test_generate_unique_id_with_large_collision_set(self):
        """generate_unique_id should handle large sets of existing IDs."""
        existing_ids = {f"base-ar-{i}" for i in range(100)}
        existing_ids.add("base-ar")

        result = generate_unique_id("base", "ar", existing_ids)
        assert result == "base-ar-100"

    def test_generate_unique_id_is_importable(self):
        """The generate_unique_id function should be importable from top-level module."""
        assert callable(generate_unique_id)
        assert generate_unique_id.__name__ == "generate_unique_id"


class TestGenerateUniqueId:
    """Tests for injection-related functions."""

    def test_generate_unique_id_no_collision(self):
        """Test unique ID generation without collision."""
        result = generate_unique_id("text", "ar", {"other"})
        assert result == "text-ar"

    def test_generate_unique_id_with_collision(self):
        """Test unique ID generation handles collisions."""
        existing = {"text-ar", "text-ar-1"}
        result = generate_unique_id("text", "ar", existing)
        assert result == "text-ar-2"

    def test_generate_unique_id_with_many_collisions(self):
        """Test unique ID generation with many existing IDs."""
        existing = {f"id-ar-{i}" for i in range(100)}
        existing.add("id-ar")
        result = generate_unique_id("id", "ar", existing)
        assert result == "id-ar-100"

    def test_generate_unique_id_empty_base(self):
        """Test unique ID generation with empty base ID."""
        result = generate_unique_id("", "ar", set())
        assert result == "-ar"

    def test_generate_unique_id_with_special_characters(self):
        """Test unique ID generation with special characters in base."""
        result = generate_unique_id("text-123", "fr", set())
        assert result == "text-123-fr"


class TestLoadAllMappings:
    """Tests for injection-related functions."""

    def test_load_all_mappings_single_json(self, temp_dir):
        """Test loading single mapping file."""
        mapping_file = temp_dir / "mapping.json"
        test_mapping = {"new": {"hello": {"ar": "مرحبا"}}}
        mapping_file.write_text(json.dumps(test_mapping, ensure_ascii=False), encoding="utf-8")
        result = load_all_mappings([mapping_file])
        assert "new" in result

        assert result == {"new": {"hello": {"ar": "مرحبا"}}}

    def test_load_all_mappings_multiple_files_merge(self, temp_dir):
        """Test loading and merging multiple mapping files."""
        m1 = temp_dir / "m1.json"
        m2 = temp_dir / "m2.json"
        m1.write_text(json.dumps({"key1": {"val": 1}}), encoding="utf-8")
        m2.write_text(json.dumps({"key2": {"val": 2}}), encoding="utf-8")
        result = load_all_mappings([m1, m2])
        assert "key1" in result
        assert "key2" in result

    def test_load_all_mappings_nonexistent_returns_empty(self, temp_dir):
        """Test loading nonexistent file returns empty dict."""
        result = load_all_mappings([temp_dir / "none.json"])
        assert result == {}

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
