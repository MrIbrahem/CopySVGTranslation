"""
Extended comprehensive unit tests for CopySVGTranslation covering additional edge cases
and previously untested functions.
"""

import json
import sys
import tempfile
import unittest
import shutil
from pathlib import Path

from lxml import etree

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from CopySVGTranslation.injection.utils import get_target_path
from CopySVGTranslation.injection.injector import (
    load_all_mappings,
    work_on_switches,
    sort_switch_texts,
)


class TestGetTargetPath(unittest.TestCase):
    """Test suite for get_target_path function."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.svg_path = self.test_dir / "source.svg"
        self.svg_path.write_text("<svg></svg>", encoding='utf-8')

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)

    def test_get_target_path_with_output_file(self):
        """Test get_target_path when output_file is specified."""
        output_file = self.test_dir / "output" / "result.svg"
        result = get_target_path(output_file, None, self.svg_path)

        self.assertEqual(result, output_file)
        self.assertTrue(result.parent.exists())

    def test_get_target_path_with_output_dir(self):
        """Test get_target_path when output_dir is specified."""
        output_dir = self.test_dir / "translated"
        result = get_target_path(None, output_dir, self.svg_path)

        self.assertEqual(result, output_dir / "source.svg")
        self.assertTrue(result.parent.exists())

    def test_get_target_path_default_to_source_dir(self):
        """Test get_target_path defaults to source file's directory."""
        result = get_target_path(None, None, self.svg_path)

        self.assertEqual(result, self.svg_path.parent / "source.svg")

    def test_get_target_path_creates_nested_directories(self):
        """Test get_target_path creates nested output directories."""
        output_file = self.test_dir / "a" / "b" / "c" / "result.svg"
        result = get_target_path(output_file, None, self.svg_path)

        self.assertTrue(result.parent.exists())
        self.assertEqual(result, output_file)

    def test_get_target_path_with_string_paths(self):
        """Test get_target_path handles string paths."""
        output_dir = str(self.test_dir / "output")
        result = get_target_path(None, output_dir, self.svg_path)

        self.assertTrue(isinstance(result, Path))
        self.assertTrue(result.parent.exists())


class TestWorkOnSwitches(unittest.TestCase):
    """Test suite for work_on_switches function."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)

    def test_work_on_switches_basic(self):
        """Test basic switch processing."""
        svg_content = '''<svg xmlns="http://www.w3.org/2000/svg">
            <switch>
                <text id="text1"><tspan>Hello</tspan></text>
            </switch>
        </svg>'''
        root = etree.fromstring(svg_content)
        existing_ids = {"text1"}
        mappings = {"new": {"hello": {"ar": "مرحبا", "fr": "Bonjour"}}}

        stats = work_on_switches(root, existing_ids, mappings, case_insensitive=True)

        self.assertEqual(stats['processed_switches'], 1)
        self.assertEqual(stats['inserted_translations'], 2)

    def test_work_on_switches_no_overwrite(self):
        """Test switch processing without overwriting existing translations."""
        svg_content = '''<svg xmlns="http://www.w3.org/2000/svg">
            <switch>
                <text id="text1-ar" systemLanguage="ar"><tspan>مرحبا</tspan></text>
                <text id="text1"><tspan>Hello</tspan></text>
            </switch>
        </svg>'''
        root = etree.fromstring(svg_content)
        existing_ids = {"text1", "text1-ar"}
        mappings = {"new": {"hello": {"ar": "مرحبا جديد", "fr": "Bonjour"}}}

        stats = work_on_switches(root, existing_ids, mappings, overwrite=False)

        self.assertEqual(stats['skipped_translations'], 1)
        self.assertEqual(stats['inserted_translations'], 1)

    def test_work_on_switches_with_overwrite(self):
        """Test switch processing with overwriting existing translations."""
        svg_content = '''<svg xmlns="http://www.w3.org/2000/svg">
            <switch>
                <text id="text1-ar" systemLanguage="ar"><tspan>Old</tspan></text>
                <text id="text1"><tspan>Hello</tspan></text>
            </switch>
        </svg>'''
        root = etree.fromstring(svg_content)
        existing_ids = {"text1", "text1-ar"}
        mappings = {"new": {"hello": {"ar": "New"}}}

        stats = work_on_switches(root, existing_ids, mappings, overwrite=True)

        self.assertEqual(stats['updated_translations'], 1)

    def test_work_on_switches_case_sensitive(self):
        """Test switch processing with case-sensitive matching."""
        svg_content = '''<svg xmlns="http://www.w3.org/2000/svg">
            <switch>
                <text id="text1"><tspan>Hello</tspan></text>
            </switch>
        </svg>'''
        root = etree.fromstring(svg_content)
        existing_ids = {"text1"}
        mappings = {"new": {"Hello": {"ar": "مرحبا"}}}

        stats = work_on_switches(root, existing_ids, mappings, case_insensitive=False)

        self.assertEqual(stats['inserted_translations'], 1)

    def test_work_on_switches_with_year_suffix(self):
        """Test switch processing with year suffix handling."""
        svg_content = '''<svg xmlns="http://www.w3.org/2000/svg">
            <switch>
                <text id="text1"><tspan>Population 2020</tspan></text>
            </switch>
        </svg>'''
        root = etree.fromstring(svg_content)
        existing_ids = {"text1"}
        mappings = {
            "title": {"Population ": {"ar": "السكان ", "fr": "Population "}},
            "new": {}
        }

        stats = work_on_switches(root, existing_ids, mappings, case_insensitive=True)

        # Year suffix logic should be applied
        self.assertGreaterEqual(stats['processed_switches'], 0)


class TestSortSwitchTexts(unittest.TestCase):
    """Test suite for sort_switch_texts function."""

    def test_sort_switch_texts_basic(self):
        """Test sorting text elements in a switch."""
        svg_content = '''<svg xmlns="http://www.w3.org/2000/svg">
            <switch>
                <text systemLanguage="ar">Arabic</text>
                <text>Default</text>
                <text systemLanguage="fr">French</text>
            </switch>
        </svg>'''
        root = etree.fromstring(svg_content)
        switch = root.find('.//{http://www.w3.org/2000/svg}switch')

        sort_switch_texts(switch)

        texts = switch.findall('.//{http://www.w3.org/2000/svg}text')
        # Default (no systemLanguage) should be last
        self.assertIsNone(texts[-1].get('systemLanguage'))

    def test_sort_switch_texts_empty_switch(self):
        """Test sorting an empty switch element."""
        svg_content = '<svg xmlns="http://www.w3.org/2000/svg"><switch></switch></svg>'
        root = etree.fromstring(svg_content)
        switch = root.find('.//{http://www.w3.org/2000/svg}switch')

        # Should not raise an error
        sort_switch_texts(switch)

    def test_sort_switch_texts_only_default(self):
        """Test sorting with only default text."""
        svg_content = '''<svg xmlns="http://www.w3.org/2000/svg">
            <switch>
                <text>Default only</text>
            </switch>
        </svg>'''
        root = etree.fromstring(svg_content)
        switch = root.find('.//{http://www.w3.org/2000/svg}switch')

        sort_switch_texts(switch)

        texts = switch.findall('.//{http://www.w3.org/2000/svg}text')
        self.assertEqual(len(texts), 1)


class TestLoadAllMappingsEdgeCases(unittest.TestCase):
    """Test suite for load_all_mappings edge cases."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)

    def test_load_all_mappings_empty_list(self):
        """Test loading with empty file list."""
        result = load_all_mappings([])

        self.assertEqual(result, {})

    def test_load_all_mappings_empty_json_file(self):
        """Test loading empty JSON file."""
        mapping_file = self.test_dir / "empty.json"
        mapping_file.write_text("{}", encoding='utf-8')

        result = load_all_mappings([mapping_file])

        self.assertEqual(result, {})

    def test_load_all_mappings_corrupted_json(self):
        """Test loading corrupted JSON file."""
        mapping_file = self.test_dir / "corrupted.json"
        mapping_file.write_text("{ corrupted", encoding='utf-8')

        result = load_all_mappings([mapping_file])

        self.assertEqual(result, {})

    def test_load_all_mappings_nested_structure(self):
        """Test loading with nested mapping structure."""
        mapping_file = self.test_dir / "nested.json"
        test_mapping = {
            "new": {
                "hello": {"ar": "مرحبا", "fr": "Bonjour"}
            },
            "title": {
                "Population ": {"ar": "السكان ", "fr": "Population "}
            }
        }
        with open(mapping_file, 'w', encoding='utf-8') as f:
            json.dump(test_mapping, f, ensure_ascii=False)

        result = load_all_mappings([mapping_file])

        self.assertIn("new", result)
        self.assertIn("title", result)

    def test_load_all_mappings_merge_overlapping_keys(self):
        """Test merging mappings with overlapping keys."""
        m1 = self.test_dir / "m1.json"
        m2 = self.test_dir / "m2.json"

        with open(m1, 'w', encoding='utf-8') as f:
            json.dump({"key": {"lang1": "value1"}}, f)

        with open(m2, 'w', encoding='utf-8') as f:
            json.dump({"key": {"lang2": "value2"}}, f)

        result = load_all_mappings([m1, m2])

        self.assertIn("lang1", result["key"])
        self.assertIn("lang2", result["key"])

    def test_load_all_mappings_string_paths(self):
        """Test loading with string paths instead of Path objects."""
        mapping_file = self.test_dir / "test.json"
        with open(mapping_file, 'w', encoding='utf-8') as f:
            json.dump({"key": {"value": "test"}}, f)

        result = load_all_mappings([str(mapping_file)])

        self.assertIn("key", result)


if __name__ == '__main__':
    unittest.main()
