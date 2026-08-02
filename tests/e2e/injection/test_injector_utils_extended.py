"""
Extended comprehensive unit tests for CopySVGTranslation covering additional edge cases
and previously untested functions.
"""

import json
import shutil
import tempfile
from pathlib import Path

import pytest
from lxml import etree

from CopySVGTranslation.injection.utils import file_langs  # noqa: F401
from CopySVGTranslation.injection.utils import generate_unique_id  # noqa: F401
from CopySVGTranslation.injection.utils import (
    get_target_path,
    load_all_mappings,
    sort_switch_texts,
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


class TestGetTargetPath(TestSetup):

    def test_get_target_path_with_output_file(self):
        """Test get_target_path when output_file is specified."""
        output_file = self.test_dir / "output" / "result.svg"
        result = get_target_path(output_file, None, self.svg_path)

        assert result == output_file
        assert result.parent.exists() is True

    def test_get_target_path_with_output_dir(self):
        """Test get_target_path when output_dir is specified."""
        output_dir = self.test_dir / "translated"
        result = get_target_path(None, output_dir, self.svg_path)

        assert result == output_dir / "source.svg"
        assert result.parent.exists() is True

    def test_get_target_path_default_to_source_dir(self):
        """Test get_target_path defaults to source file's directory."""
        result = get_target_path(None, None, self.svg_path)

        assert result == self.svg_path.parent / "source.svg"

    def test_get_target_path_creates_nested_directories(self):
        """Test get_target_path creates nested output directories."""
        output_file = self.test_dir / "a" / "b" / "c" / "result.svg"
        result = get_target_path(output_file, None, self.svg_path)

        assert result.parent.exists() is True
        assert result == output_file

    def test_get_target_path_with_string_paths(self):
        """Test get_target_path handles string paths."""
        output_dir = str(self.test_dir / "output")
        result = get_target_path(None, output_dir, self.svg_path)

        assert isinstance(result, Path) is True
        assert result.parent.exists() is True


class TestSortSwitchTexts(TestSetup):
    """Test suite for sort_switch_texts function."""

    def test_sort_switch_texts_basic(self):
        """Test sorting text elements in a switch."""
        svg_content = """<svg xmlns="http://www.w3.org/2000/svg">
            <switch>
                <text systemLanguage="ar">Arabic</text>
                <text>Default</text>
                <text systemLanguage="fr">French</text>
            </switch>
        </svg>"""
        root = etree.fromstring(svg_content)
        switch = root.find(".//{http://www.w3.org/2000/svg}switch")
        assert switch is not None

        sort_switch_texts(switch)

        texts = switch.findall(".//{http://www.w3.org/2000/svg}text")
        # Default (no systemLanguage) should be last
        assert texts[-1].get("systemLanguage") is None

    def test_sort_switch_texts_empty_switch(self):
        """Test sorting an empty switch element."""
        svg_content = '<svg xmlns="http://www.w3.org/2000/svg"><switch></switch></svg>'
        root = etree.fromstring(svg_content)
        switch = root.find(".//{http://www.w3.org/2000/svg}switch")
        assert switch is not None

        # Should not raise an error
        sort_switch_texts(switch)

    def test_sort_switch_texts_only_default(self):
        """Test sorting with only default text."""
        svg_content = """<svg xmlns="http://www.w3.org/2000/svg">
            <switch>
                <text>Default only</text>
            </switch>
        </svg>"""
        root = etree.fromstring(svg_content)
        switch = root.find(".//{http://www.w3.org/2000/svg}switch")
        assert switch is not None

        sort_switch_texts(switch)

        texts = switch.findall(".//{http://www.w3.org/2000/svg}text")
        assert len(texts) == 1


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

    def test_load_all_mappings_string_paths(self):
        """Test loading with string paths instead of Path objects."""
        mapping_file = self.test_dir / "test.json"
        with open(mapping_file, "w", encoding="utf-8") as f:
            json.dump({"key": {"value": "test"}}, f)

        result = load_all_mappings([str(mapping_file)])

        assert "key" in result
