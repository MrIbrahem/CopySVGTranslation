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
from CopySVGTranslation.injection import (
    SvgStructureException,
)
from CopySVGTranslation.injection.preparation import (
    normalize_lang,
    get_text_content,
    clone_element,
    reorder_texts,
    make_translation_ready,
)


class TestReorderTexts(unittest.TestCase):
    """Test suite for reorder_texts function."""

    def test_reorder_texts_no_switches(self):
        """Test reordering with no switch elements."""
        svg_content = '<svg xmlns="http://www.w3.org/2000/svg"><text>No switch</text></svg>'
        root = etree.fromstring(svg_content)

        # Should not raise an error
        reorder_texts(root)


class TestNormalizeLang(unittest.TestCase):
    """Test suite for normalize_lang function."""

    def test_normalize_lang_simple_code(self):
        """Test normalization of simple language code."""
        self.assertEqual(normalize_lang("EN"), "en")
        self.assertEqual(normalize_lang("FR"), "fr")
        self.assertEqual(normalize_lang("ar"), "ar")

    def test_normalize_lang_with_region(self):
        """Test normalization with region code."""
        self.assertEqual(normalize_lang("en-US"), "en-US")
        self.assertEqual(normalize_lang("en_us"), "en-US")
        self.assertEqual(normalize_lang("pt_br"), "pt-BR")
        self.assertEqual(normalize_lang("zh-cn"), "zh-CN")

    def test_normalize_lang_complex_format(self):
        """Test normalization with complex format."""
        self.assertEqual(normalize_lang("en-us-variant"), "en-US-Variant")

    def test_normalize_lang_empty_string(self):
        """Test normalization of empty string."""
        self.assertEqual(normalize_lang(""), "")

    def test_normalize_lang_with_whitespace(self):
        """Test normalization handles whitespace."""
        self.assertEqual(normalize_lang("  en-US  "), "en-US")
        self.assertEqual(normalize_lang("en us"), "en-US")

    def test_normalize_lang_hyphen_variations(self):
        """Test different hyphen/underscore variations."""
        self.assertEqual(normalize_lang("en-GB"), "en-GB")
        self.assertEqual(normalize_lang("en_GB"), "en-GB")


class TestGetTextContent(unittest.TestCase):
    """Test suite for get_text_content function."""

    def test_get_text_content_simple(self):
        """Test getting text content from simple element."""
        xml = '<text xmlns="http://www.w3.org/2000/svg">Hello</text>'
        elem = etree.fromstring(xml)
        result = get_text_content(elem)

        self.assertEqual(result, "Hello")

    def test_get_text_content_with_children(self):
        """Test getting text content with child elements."""
        xml = '''<text xmlns="http://www.w3.org/2000/svg">
            Hello <tspan>World</tspan> Test
        </text>'''
        elem = etree.fromstring(xml)
        result = get_text_content(elem)

        self.assertIn("Hello", result)
        self.assertIn("World", result)
        self.assertIn("Test", result)

    def test_get_text_content_empty(self):
        """Test getting text content from empty element."""
        xml = '<text xmlns="http://www.w3.org/2000/svg"></text>'
        elem = etree.fromstring(xml)
        result = get_text_content(elem)

        self.assertEqual(result, "")

    def test_get_text_content_nested_structure(self):
        """Test getting text content with nested structure."""
        xml = '''<text xmlns="http://www.w3.org/2000/svg">
            <tspan>First<tspan>Nested</tspan></tspan>
        </text>'''
        elem = etree.fromstring(xml)
        result = get_text_content(elem)

        self.assertIn("First", result)
        self.assertIn("Nested", result)


class TestCloneElement(unittest.TestCase):
    """Test suite for clone_element function."""

    def test_clone_element_basic(self):
        """Test cloning a basic element."""
        xml = '<text id="text1" xmlns="http://www.w3.org/2000/svg">Hello</text>'
        elem = etree.fromstring(xml)
        cloned = clone_element(elem)

        self.assertEqual(cloned.get('id'), 'text1')
        self.assertEqual(cloned.text, 'Hello')
        self.assertIsNot(cloned, elem)

    def test_clone_element_with_children(self):
        """Test cloning element with children."""
        xml = '''<text xmlns="http://www.w3.org/2000/svg">
            <tspan id="t1">First</tspan>
            <tspan id="t2">Second</tspan>
        </text>'''
        elem = etree.fromstring(xml)
        cloned = clone_element(elem)

        children = cloned.findall('{http://www.w3.org/2000/svg}tspan')
        self.assertEqual(len(children), 2)
        self.assertEqual(children[0].get('id'), 't1')
        self.assertEqual(children[1].get('id'), 't2')

    def test_clone_element_deep_copy(self):
        """Test that clone is a deep copy."""
        xml = '<text id="text1" xmlns="http://www.w3.org/2000/svg"><tspan>Test</tspan></text>'
        elem = etree.fromstring(xml)
        cloned = clone_element(elem)

        # Modify original
        elem.set('id', 'modified')

        # Clone should be unchanged
        self.assertEqual(cloned.get('id'), 'text1')

    def test_clone_element_with_attributes(self):
        """Test cloning preserves all attributes."""
        xml = '<text id="t1" class="label" x="10" y="20" xmlns="http://www.w3.org/2000/svg">Test</text>'
        elem = etree.fromstring(xml)
        cloned = clone_element(elem)

        self.assertEqual(cloned.get('id'), 't1')
        self.assertEqual(cloned.get('class'), 'label')
        self.assertEqual(cloned.get('x'), '10')
        self.assertEqual(cloned.get('y'), '20')


class TestMakeTranslationReadyEdgeCases(unittest.TestCase):
    """Test suite for make_translation_ready edge cases."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)

    def test_make_translation_ready_with_tref(self):
        """Test that SVG with tref raises exception."""
        svg_path = self.test_dir / "test.svg"
        svg_content = '''<svg xmlns="http://www.w3.org/2000/svg">
            <text><tref href="#someref"/></text>
        </svg>'''
        svg_path.write_text(svg_content, encoding='utf-8')

        with self.assertRaises(SvgStructureException) as ctx:
            make_translation_ready(svg_path)

        self.assertIn('tref', str(ctx.exception))

    def test_make_translation_ready_with_css_ids(self):
        """Test that CSS with ID selectors raises exception."""
        svg_path = self.test_dir / "test.svg"
        svg_content = '''<svg xmlns="http://www.w3.org/2000/svg">
            <style>#myid { fill: red; }</style>
            <text id="myid">Test</text>
        </svg>'''
        svg_path.write_text(svg_content, encoding='utf-8')

        with self.assertRaises(SvgStructureException) as ctx:
            make_translation_ready(svg_path)

        self.assertIn('css', str(ctx.exception).lower())

    def test_make_translation_ready_with_dollar_sign(self):
        """Test that text with dollar signs raises exception."""
        svg_path = self.test_dir / "test.svg"
        svg_content = '''<svg xmlns="http://www.w3.org/2000/svg">
            <text>Price: $10</text>
        </svg>'''
        svg_path.write_text(svg_content, encoding='utf-8')

        with self.assertRaises(SvgStructureException) as ctx:
            make_translation_ready(svg_path)

        self.assertIn('dollar', str(ctx.exception).lower())

    def test_make_translation_ready_nested_tspans(self):
        """Test that nested tspans raise exception."""
        svg_path = self.test_dir / "test.svg"
        svg_content = '''<svg xmlns="http://www.w3.org/2000/svg">
            <text><tspan>Outer<tspan>Inner</tspan></tspan></text>
        </svg>'''
        svg_path.write_text(svg_content, encoding='utf-8')

        with self.assertRaises(SvgStructureException) as ctx:
            make_translation_ready(svg_path)

        self.assertIn('nested', str(ctx.exception).lower())

    def test_make_translation_ready_wraps_raw_text(self):
        """Test that raw text in text elements is wrapped in tspans."""
        svg_path = self.test_dir / "test.svg"
        svg_content = '''<svg xmlns="http://www.w3.org/2000/svg">
            <text>Raw text content</text>
        </svg>'''
        svg_path.write_text(svg_content, encoding='utf-8')

        _tree, root = make_translation_ready(svg_path)

        text_elem = root.find('.//{http://www.w3.org/2000/svg}text')
        tspans = text_elem.findall('{http://www.w3.org/2000/svg}tspan')
        self.assertGreater(len(tspans), 0)

    def test_make_translation_ready_creates_switch(self):
        """Test that text elements are wrapped in switch elements."""
        svg_path = self.test_dir / "test.svg"
        svg_content = '''<svg xmlns="http://www.w3.org/2000/svg">
            <g><text id="t1">Content</text></g>
        </svg>'''
        svg_path.write_text(svg_content, encoding='utf-8')

        _tree, root = make_translation_ready(svg_path)

        switches = root.findall('.//{http://www.w3.org/2000/svg}switch')
        self.assertGreater(len(switches), 0)

    def test_make_translation_ready_assigns_ids(self):
        """Test that missing IDs are assigned."""
        svg_path = self.test_dir / "test.svg"
        svg_content = '''<svg xmlns="http://www.w3.org/2000/svg">
            <text>No ID</text>
        </svg>'''
        svg_path.write_text(svg_content, encoding='utf-8')

        _tree, root = make_translation_ready(svg_path)

        text_elem = root.find('.//{http://www.w3.org/2000/svg}text')
        self.assertIsNotNone(text_elem.get('id'))

    def test_make_translation_ready_duplicate_lang_error(self):
        """Test that duplicate language codes in switch raise exception."""
        svg_path = self.test_dir / "test.svg"
        svg_content = '''<svg xmlns="http://www.w3.org/2000/svg">
            <switch>
                <text systemLanguage="ar">Arabic 1</text>
                <text systemLanguage="ar">Arabic 2</text>
            </switch>
        </svg>'''
        svg_path.write_text(svg_content, encoding='utf-8')

        with self.assertRaises(SvgStructureException) as ctx:
            make_translation_ready(svg_path)

        self.assertIn('lang', str(ctx.exception).lower())

    def test_make_translation_ready_splits_comma_langs(self):
        """Test that comma-separated languages are split."""
        svg_path = self.test_dir / "test.svg"
        svg_content = '''<svg xmlns="http://www.w3.org/2000/svg">
            <switch>
                <text systemLanguage="ar,fr">Multi</text>
                <text>Default</text>
            </switch>
        </svg>'''
        svg_path.write_text(svg_content, encoding='utf-8')

        _tree, root = make_translation_ready(svg_path)

        switch = root.find('.//{http://www.w3.org/2000/svg}switch')
        text_elems = switch.findall('{http://www.w3.org/2000/svg}text')

        # Should have split into separate text elements
        self.assertGreater(len(text_elems), 2)

    def test_make_translation_ready_invalid_node_id(self):
        """Test that invalid node IDs raise exception."""
        svg_path = self.test_dir / "test.svg"
        svg_content = '''<svg xmlns="http://www.w3.org/2000/svg">
            <text id="invalid|id">Test</text>
        </svg>'''
        svg_path.write_text(svg_content, encoding='utf-8')

        with self.assertRaises(SvgStructureException) as ctx:
            make_translation_ready(svg_path)

        self.assertIn('id', str(ctx.exception).lower())


if __name__ == '__main__':
    unittest.main()
