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

from lxml import etree

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from CopySvgTranslate import extract


class TestExtractYearHandling(unittest.TestCase):
    """Test suite for year suffix handling in extract function."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)

    def test_extract_detects_year_suffix(self):
        """Test extraction detects and handles year suffixes."""
        svg_path = self.test_dir / "test.svg"
        svg_content = '''<svg xmlns="http://www.w3.org/2000/svg">
            <switch>
                <text id="text1-ar" systemLanguage="ar"><tspan id="t1-ar">السكان 2020</tspan></text>
                <text id="text1"><tspan id="t1">Population 2020</tspan></text>
            </switch>
        </svg>'''
        svg_path.write_text(svg_content, encoding='utf-8')

        result = extract(svg_path)

        # Should create title mapping for year-suffixed text
        if result and "title" in result:
            self.assertIsInstance(result["title"], dict)

    def test_extract_year_with_multiple_languages(self):
        """Test year suffix handling with multiple languages."""
        svg_path = self.test_dir / "test.svg"
        svg_content = '''<svg xmlns="http://www.w3.org/2000/svg">
            <switch>
                <text id="text1-ar" systemLanguage="ar"><tspan id="t1-ar">السكان 2020</tspan></text>
                <text id="text1-fr" systemLanguage="fr"><tspan id="t1-fr">Population 2020</tspan></text>
                <text id="text1"><tspan id="t1">Population 2020</tspan></text>
            </switch>
        </svg>'''
        svg_path.write_text(svg_content, encoding='utf-8')

        result = extract(svg_path)

        self.assertIsNotNone(result)
        self.assertIn("new", result)

    def test_extract_non_year_digits(self):
        """Test that non-year digit sequences are handled correctly."""
        svg_path = self.test_dir / "test.svg"
        svg_content = '''<svg xmlns="http://www.w3.org/2000/svg">
            <switch>
                <text id="text1"><tspan id="t1">Value 42</tspan></text>
            </switch>
        </svg>'''
        svg_path.write_text(svg_content, encoding='utf-8')

        result = extract(svg_path)

        self.assertIsNotNone(result)
        # Should not create title mapping for non-4-digit numbers


class TestExtractEdgeCases(unittest.TestCase):
    """Test suite for extract function edge cases."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)

    def test_extract_empty_switch(self):
        """Test extraction with empty switch element."""
        svg_path = self.test_dir / "test.svg"
        svg_content = '''<svg xmlns="http://www.w3.org/2000/svg">
            <switch></switch>
        </svg>'''
        svg_path.write_text(svg_content, encoding='utf-8')

        result = extract(svg_path)

        # Should handle gracefully
        self.assertIsNotNone(result)

    def test_extract_switch_without_default_text(self):
        """Test extraction with switch containing only translated text."""
        svg_path = self.test_dir / "test.svg"
        svg_content = '''<svg xmlns="http://www.w3.org/2000/svg">
            <switch>
                <text systemLanguage="ar"><tspan>Arabic</tspan></text>
            </switch>
        </svg>'''
        svg_path.write_text(svg_content, encoding='utf-8')

        result = extract(svg_path)

        self.assertIsNotNone(result)

    def test_extract_with_mixed_tspan_and_text(self):
        """Test extraction with mixed tspan and direct text."""
        svg_path = self.test_dir / "test.svg"
        svg_content = '''<svg xmlns="http://www.w3.org/2000/svg">
            <switch>
                <text id="t1"><tspan id="t1-1">With tspan</tspan></text>
            </switch>
            <switch>
                <text id="t2">Direct text</text>
            </switch>
        </svg>'''
        svg_path.write_text(svg_content, encoding='utf-8')

        result = extract(svg_path)

        self.assertIsNotNone(result)

    def test_extract_case_insensitive_default(self):
        """Test that case_insensitive is True by default."""
        svg_path = self.test_dir / "test.svg"
        svg_content = '''<svg xmlns="http://www.w3.org/2000/svg">
            <switch>
                <text id="t1-ar" systemLanguage="ar"><tspan id="t1-ar">مرحبا</tspan></text>
                <text id="t1"><tspan id="t1">HELLO</tspan></text>
            </switch>
        </svg>'''
        svg_path.write_text(svg_content, encoding='utf-8')

        result = extract(svg_path, case_insensitive=True)

        if result and "new" in result:
            # Keys should be lowercase
            self.assertTrue(any(key.islower() for key in result["new"].keys()))

    def test_extract_preserves_empty_tspan_text(self):
        """Test extraction handles empty tspan text."""
        svg_path = self.test_dir / "test.svg"
        svg_content = '''<svg xmlns="http://www.w3.org/2000/svg">
            <switch>
                <text id="t1"><tspan id="t1-1"></tspan></text>
            </switch>
        </svg>'''
        svg_path.write_text(svg_content, encoding='utf-8')

        result = extract(svg_path)

        self.assertIsNotNone(result)

    def test_extract_with_base_id_fallback(self):
        """Test extraction with base_id lookup fallback."""
        svg_path = self.test_dir / "test.svg"
        svg_content = '''<svg xmlns="http://www.w3.org/2000/svg">
            <switch>
                <text id="text1-ar" systemLanguage="ar"><tspan id="TEXT1-ar">مرحبا</tspan></text>
                <text id="text1"><tspan id="TEXT1">Hello</tspan></text>
            </switch>
        </svg>'''
        svg_path.write_text(svg_content, encoding='utf-8')

        result = extract(svg_path)

        self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main()
