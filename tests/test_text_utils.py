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

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from CopySVGTranslation.text_utils import extract_text_from_node


class TestExtractTextFromNode(unittest.TestCase):
    """Test suite for extract_text_from_node function."""

    def test_extract_from_text_with_tspans(self):
        """Test extraction from text element with tspan children."""
        xml = '''<text xmlns="http://www.w3.org/2000/svg">
            <tspan>First</tspan>
            <tspan>Second</tspan>
        </text>'''
        node = etree.fromstring(xml)
        result = extract_text_from_node(node)

        self.assertEqual(result, ["First", "Second"])

    def test_extract_from_text_without_tspans(self):
        """Test extraction from text element without tspans."""
        xml = '<text xmlns="http://www.w3.org/2000/svg">Direct text</text>'
        node = etree.fromstring(xml)
        result = extract_text_from_node(node)

        self.assertEqual(result, ["Direct text"])

    def test_extract_from_text_with_empty_tspans(self):
        """Test extraction with empty tspan elements."""
        xml = '''<text xmlns="http://www.w3.org/2000/svg">
            <tspan></tspan>
            <tspan>Content</tspan>
        </text>'''
        node = etree.fromstring(xml)
        result = extract_text_from_node(node)

        self.assertEqual(result, ["", "Content"])

    def test_extract_from_text_with_whitespace_tspans(self):
        """Test extraction handles whitespace in tspans."""
        xml = '''<text xmlns="http://www.w3.org/2000/svg">
            <tspan>  Spaces  </tspan>
            <tspan>	Tabs	</tspan>
        </text>'''
        node = etree.fromstring(xml)
        result = extract_text_from_node(node)

        self.assertEqual(result, ["Spaces", "Tabs"])

    def test_extract_from_empty_text_node(self):
        """Test extraction from empty text node."""
        xml = '<text xmlns="http://www.w3.org/2000/svg"></text>'
        node = etree.fromstring(xml)
        result = extract_text_from_node(node)

        self.assertEqual(result, [""])

    def test_extract_with_unicode_content(self):
        """Test extraction with Unicode content."""
        xml = '''<text xmlns="http://www.w3.org/2000/svg">
            <tspan>مرحبا</tspan>
            <tspan>你好</tspan>
            <tspan>Привет</tspan>
        </text>'''
        node = etree.fromstring(xml)
        result = extract_text_from_node(node)

        self.assertEqual(result, ["مرحبا", "你好", "Привет"])


if __name__ == '__main__':
    unittest.main()
