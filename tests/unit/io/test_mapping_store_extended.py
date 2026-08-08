"""
Unit tests for CopySVGTranslation/io/mapping_store.py module.
"""

import json
import shutil
import tempfile
from collections.abc import Iterable
from pathlib import Path

import pytest

from CopySVGTranslation.io.mapping_store import MappingStore


def load_all_mappings(mapping_files: Iterable[Path | str]) -> dict:
    """Load and merge translation mapping JSON files into a single dictionary."""

    store = MappingStore()

    mapping_obj = store.load_many(mapping_files)

    # mapping = mapping_obj.to_json()

    return mapping_obj.new


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
        }
        with open(mapping_file, "w", encoding="utf-8") as f:
            json.dump(test_mapping, f, ensure_ascii=False)

        result = load_all_mappings([mapping_file])

        assert result == {"hello": {"ar": "مرحبا", "fr": "Bonjour"}}

    def test_load_all_mappings_merge_overlapping_keys(self):
        """Test merging mappings with overlapping keys."""
        m1 = self.test_dir / "m1.json"
        m2 = self.test_dir / "m2.json"

        with open(m1, "w", encoding="utf-8") as f:
            json.dump({"key": {"lang1": "value1"}}, f)

        with open(m2, "w", encoding="utf-8") as f:
            json.dump({"key": {"lang2": "value2"}}, f)

        result = load_all_mappings([m1, m2])

        assert "key" not in result

    def test_load_all_mappings_string_paths(self):
        """Test loading with string paths instead of Path objects."""
        mapping_file = self.test_dir / "test.json"
        with open(mapping_file, "w", encoding="utf-8") as f:
            json.dump({"key": {"value": "test"}}, f)

        result = load_all_mappings([str(mapping_file)])

        assert "key" not in result


class TestLoadAllMappings:
    """Tests for injection-related functions."""

    def test_load_all_mappings_single_json(self, temp_dir):
        """Test loading single mapping file."""
        mapping_file = temp_dir / "mapping.json"
        test_mapping = {"new": {"hello": {"ar": "مرحبا"}}}
        mapping_file.write_text(json.dumps(test_mapping, ensure_ascii=False), encoding="utf-8")
        result = load_all_mappings([mapping_file])

        assert result == {"hello": {"ar": "مرحبا"}}

    def test_load_all_mappings_multiple_files_merge(self, temp_dir):
        """Test loading and merging multiple mapping files."""
        m1 = temp_dir / "m1.json"
        m2 = temp_dir / "m2.json"
        m1.write_text(json.dumps({"key1": {"val": 1}}), encoding="utf-8")
        m2.write_text(json.dumps({"key2": {"val": 2}}), encoding="utf-8")
        result = load_all_mappings([m1, m2])
        assert "key1" not in result
        assert "key2" not in result

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

        assert result["hello"]["ar"] == "مرحبا"

        assert result == {"hello": {"ar": "مرحبا"}}

    def test_load_all_mappings_multiple_files(self, temp_dir):
        """Test loading multiple mapping files."""
        m1 = temp_dir / "m1.json"
        m2 = temp_dir / "m2.json"
        m1.write_text(json.dumps({"key1": {"value": 1}}), encoding="utf-8")
        m2.write_text(json.dumps({"key2": {"value": 2}}), encoding="utf-8")
        result = load_all_mappings([m1, m2])
        assert "key1" not in result
        assert "key2" not in result

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
        assert "lang1" not in result
        assert "lang2" not in result
