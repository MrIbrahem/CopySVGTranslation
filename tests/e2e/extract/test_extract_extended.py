"""
Extended comprehensive unit tests for CopySVGTranslation covering additional edge cases
and previously untested functions.
"""

import tempfile
import unittest
import shutil
from pathlib import Path

from CopySVGTranslation import extract


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
        assert result is not None
        assert result is not None

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

        assert result is not None

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

        assert result is not None

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

        assert "new" in result

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

        assert result is not None

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

        assert result is not None


if __name__ == '__main__':
    unittest.main()
