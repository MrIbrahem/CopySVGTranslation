# ruff: noqa: F401
"""
Unit tests for CopySVGTranslation/injection/utils.py module.


TODO: write tests
"""

import json

from CopySVGTranslation.utils.injection_utils import (
    generate_unique_id,
    get_target_path,
    load_all_mappings,
)


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
