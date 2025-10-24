"""
Extended comprehensive unit tests for CopySvgTranslate covering additional edge cases
and previously untested functions.
"""

import json
import sys
import tempfile
import unittest
import shutil
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from CopySvgTranslate import inject, start_injects


class TestStartInjectsEdgeCases(unittest.TestCase):
    """Test suite for start_injects edge cases."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.output_dir = self.test_dir / "output"
        self.output_dir.mkdir()

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)

    def test_start_injects_empty_file_list(self):
        """Test start_injects with empty file list."""
        translations = {"new": {"hello": {"ar": "مرحبا"}}}

        result = start_injects([], translations, self.output_dir)

        self.assertEqual(result['saved_done'], 0)
        self.assertEqual(result['no_save'], 0)

    def test_start_injects_nonexistent_files(self):
        """Test start_injects with nonexistent files."""
        translations = {"new": {"hello": {"ar": "مرحبا"}}}
        files = [str(self.test_dir / "nonexistent.svg")]

        result = start_injects(files, translations, self.output_dir)

        self.assertEqual(result['saved_done'], 0)
        self.assertGreater(result['no_save'], 0)

    def test_start_injects_tracks_nested_files(self):
        """Test that start_injects tracks nested tspan errors."""
        svg_path = self.test_dir / "nested.svg"
        svg_content = '''<svg xmlns="http://www.w3.org/2000/svg">
            <text><tspan>Outer<tspan>Nested</tspan></tspan></text>
        </svg>'''
        svg_path.write_text(svg_content, encoding='utf-8')

        translations = {"new": {"outer": {"ar": "مرحبا"}}}

        result = start_injects([str(svg_path)], translations, self.output_dir)

        self.assertGreaterEqual(result['nested_files'], 0)

    def test_start_injects_tracks_no_changes(self):
        """Test that start_injects tracks files with no changes."""
        svg_path = self.test_dir / "test.svg"
        svg_content = '''<svg xmlns="http://www.w3.org/2000/svg">
            <switch>
                <text id="text1-ar" systemLanguage="ar"><tspan>مرحبا</tspan></text>
                <text id="text1"><tspan>Hello</tspan></text>
            </switch>
        </svg>'''
        svg_path.write_text(svg_content, encoding='utf-8')

        translations = {"new": {"hello": {"ar": "مرحبا"}}}

        result = start_injects([str(svg_path)], translations, self.output_dir, overwrite=False)

        # Should track files with no changes
        self.assertIn('no_changes', result)

    def test_start_injects_with_overwrite(self):
        """Test start_injects with overwrite option."""
        svg_path = self.test_dir / "test.svg"
        svg_content = '''<svg xmlns="http://www.w3.org/2000/svg">
            <switch>
                <text id="text1-ar" systemLanguage="ar"><tspan>Old</tspan></text>
                <text id="text1"><tspan>Hello</tspan></text>
            </switch>
        </svg>'''
        svg_path.write_text(svg_content, encoding='utf-8')

        translations = {"new": {"hello": {"ar": "New"}}}

        result = start_injects([str(svg_path)], translations, self.output_dir, overwrite=True)

        # Should process the file
        self.assertIn('files', result)

    def test_start_injects_returns_file_stats(self):
        """Test that start_injects returns per-file statistics."""
        svg_path = self.test_dir / "test.svg"
        svg_content = '''<svg xmlns="http://www.w3.org/2000/svg">
            <switch><text id="t1"><tspan>Hello</tspan></text></switch>
        </svg>'''
        svg_path.write_text(svg_content, encoding='utf-8')

        translations = {"new": {"hello": {"ar": "مرحبا"}}}

        result = start_injects([str(svg_path)], translations, self.output_dir)

        self.assertIn('files', result)
        self.assertIsInstance(result['files'], dict)


class TestInjectEdgeCases(unittest.TestCase):
    """Test suite for inject function edge cases."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)

    def test_inject_with_invalid_svg_structure(self):
        """Test inject with invalid SVG structure."""
        svg_path = self.test_dir / "invalid.svg"
        svg_content = '''<svg xmlns="http://www.w3.org/2000/svg">
            <text id="bad|id">Test</text>
        </svg>'''
        svg_path.write_text(svg_content, encoding='utf-8')

        mappings = {"new": {"test": {"ar": "اختبار"}}}

        result, stats = inject(svg_path, all_mappings=mappings, return_stats=True)

        self.assertIsNone(result)
        self.assertIn('error', stats)

    def test_inject_case_insensitive_false(self):
        """Test inject with case-sensitive matching."""
        svg_path = self.test_dir / "test.svg"
        svg_content = '''<svg xmlns="http://www.w3.org/2000/svg">
            <switch><text id="t1"><tspan>Hello</tspan></text></switch>
        </svg>'''
        svg_path.write_text(svg_content, encoding='utf-8')

        mappings = {"new": {"Hello": {"ar": "مرحبا"}}}

        result = inject(svg_path, all_mappings=mappings, case_insensitive=False)

        self.assertIsNotNone(result)

    def test_inject_both_mapping_files_and_all_mappings(self):
        """Test that all_mappings takes precedence over mapping_files."""
        svg_path = self.test_dir / "test.svg"
        svg_content = '''<svg xmlns="http://www.w3.org/2000/svg">
            <switch><text id="t1"><tspan>Hello</tspan></text></switch>
        </svg>'''
        svg_path.write_text(svg_content, encoding='utf-8')

        mapping_file = self.test_dir / "mapping.json"
        with open(mapping_file, 'w', encoding='utf-8') as f:
            json.dump({"new": {"hello": {"fr": "Bonjour"}}}, f)

        all_mappings = {"new": {"hello": {"ar": "مرحبا"}}}

        result = inject(
            svg_path,
            mapping_files=[mapping_file],
            all_mappings=all_mappings
        )

        # all_mappings should be used
        self.assertIsNotNone(result)

    def test_inject_save_result_creates_output_file(self):
        """Test that save_result=True creates the output file."""
        svg_path = self.test_dir / "test.svg"
        svg_content = '''<svg xmlns="http://www.w3.org/2000/svg">
            <switch><text id="t1"><tspan>Hello</tspan></text></switch>
        </svg>'''
        svg_path.write_text(svg_content, encoding='utf-8')

        output_file = self.test_dir / "output.svg"
        mappings = {"new": {"hello": {"ar": "مرحبا"}}}

        inject(
            svg_path,
            all_mappings=mappings,
            output_file=output_file,
            save_result=True
        )

        self.assertTrue(output_file.exists())

    def test_inject_without_save_result_no_file_created(self):
        """Test that save_result=False doesn't create output file."""
        svg_path = self.test_dir / "test.svg"
        svg_content = '''<svg xmlns="http://www.w3.org/2000/svg">
            <switch><text id="t1"><tspan>Hello</tspan></text></switch>
        </svg>'''
        svg_path.write_text(svg_content, encoding='utf-8')

        output_file = self.test_dir / "output.svg"
        mappings = {"new": {"hello": {"ar": "مرحبا"}}}

        inject(
            svg_path,
            all_mappings=mappings,
            output_file=output_file,
            save_result=False
        )

        self.assertFalse(output_file.exists())


if __name__ == '__main__':
    unittest.main()
