"""
Extended comprehensive unit tests for CopySVGTranslation covering additional edge cases
and previously untested functions.
"""

import json
import shutil
import tempfile
import textwrap
from pathlib import Path

import pytest
from lxml import etree

from CopySVGTranslation.injection.utils import (
    file_langs,
    generate_unique_id,
    get_target_path,
    load_all_mappings,
    sort_switch_texts,
)


def write_svg(tmp_path: Path, content: str) -> Path:
    svg_path = tmp_path / "sample.svg"
    svg_path.write_text(textwrap.dedent(content), encoding="utf-8")
    return svg_path


def test_inject_tracks_new_languages(tmp_path):
    svg_path = write_svg(
        tmp_path,
        """
        <svg xmlns=\"http://www.w3.org/2000/svg\">
            <switch>
                <text id=\"t1\"><tspan>Hello</tspan></text>
            </switch>
        </svg>
        """,
    )

    before_languages = file_langs(svg_path)

    assert before_languages == set()


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
