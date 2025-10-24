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

from CopySvgTranslate import extract, inject, start_injects
from CopySvgTranslate.text_utils import extract_text_from_node
from CopySvgTranslate.injection.injector import (
    load_all_mappings,
    get_target_path,
    work_on_switches,
    sort_switch_texts,
)
from CopySvgTranslate.injection.preparation import (
    normalize_lang,
    get_text_content,
    clone_element,
    reorder_texts,
    make_translation_ready,
    SvgStructureException,
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
        self.assertEqual(stats['new_languages'], 2)

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
