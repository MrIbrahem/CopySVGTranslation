"""
Extended comprehensive unit tests for CopySVGTranslation covering additional edge cases
and previously untested functions.
"""

import tempfile
import unittest
import shutil
from pathlib import Path

from CopySVGTranslation import extract


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
        self.assertIsInstance(result["title"], dict)

        assert result["title"] == {'population': {'ar': 'السكان'}}

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
        self.assertIn("title", result)

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


if __name__ == '__main__':
    unittest.main()
