"""Additional comprehensive unit tests for SvgTranslate."""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from lxml import etree

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from SvgTranslate import extract, inject, normalize_text, generate_unique_id
from SvgTranslate.text_utils import extract_text_from_node
from SvgTranslate.injection.injector import load_all_mappings
from SvgTranslate.injection.preparation import normalize_lang, get_text_content, clone_element, SvgStructureException
from SvgTranslate.workflows import svg_extract_and_injects


class TestTextUtilsComprehensive(unittest.TestCase):
    """Comprehensive tests for text utility functions."""

    def test_normalize_text_tabs_newlines(self):
        """Test normalization with tabs and newlines."""
        self.assertEqual(normalize_text("hello\t\nworld"), "hello world")
        self.assertEqual(normalize_text("  hello\n\n  world  "), "hello world")

    def test_normalize_text_case_insensitive_variations(self):
        """Test case-insensitive normalization variations."""
        self.assertEqual(normalize_text("Hello World", case_insensitive=True), "hello world")
        self.assertEqual(normalize_text("HELLO WORLD", case_insensitive=True), "hello world")

    def test_normalize_text_unicode_chars(self):
        """Test normalization with Unicode characters."""
        self.assertEqual(normalize_text("  مرحبا  بك  "), "مرحبا بك")
        self.assertEqual(normalize_text("  你好  世界  "), "你好 世界")

    def test_extract_text_from_node_with_multiple_tspans(self):
        """Test extracting text from node with multiple tspans."""
        svg_ns = "http://www.w3.org/2000/svg"
        text_node = etree.fromstring(f'<text xmlns="{svg_ns}"><tspan>Hello</tspan><tspan>World</tspan></text>')
        result = extract_text_from_node(text_node)
        self.assertEqual(result, ["Hello", "World"])

    def test_extract_text_from_node_plain_text(self):
        """Test extracting plain text from node without tspans."""
        svg_ns = "http://www.w3.org/2000/svg"
        text_node = etree.fromstring(f'<text xmlns="{svg_ns}">Plain text</text>')
        result = extract_text_from_node(text_node)
        self.assertEqual(result, ["Plain text"])


class TestPreparationFunctions(unittest.TestCase):
    """Tests for SVG preparation utility functions."""

    def test_normalize_lang_simple_codes(self):
        """Test normalizing simple language codes."""
        self.assertEqual(normalize_lang("en"), "en")
        self.assertEqual(normalize_lang("AR"), "ar")
        self.assertEqual(normalize_lang("FR"), "fr")

    def test_normalize_lang_with_region_codes(self):
        """Test normalizing language codes with regions."""
        self.assertEqual(normalize_lang("en_US"), "en-US")
        self.assertEqual(normalize_lang("en-GB"), "en-GB")
        self.assertEqual(normalize_lang("zh_CN"), "zh-CN")

    def test_normalize_lang_complex_codes(self):
        """Test normalizing complex language codes."""
        self.assertEqual(normalize_lang("en_US_POSIX"), "en-US-Posix")

    def test_get_text_content_with_tspans(self):
        """Test getting text content from elements with nested tspans."""
        svg_ns = "http://www.w3.org/2000/svg"
        element = etree.fromstring(f'<text xmlns="{svg_ns}">Hello <tspan>World</tspan> Test</text>')
        result = get_text_content(element)
        self.assertIn("Hello", result)
        self.assertIn("World", result)

    def test_clone_element_creates_copy(self):
        """Test element cloning creates independent copy."""
        svg_ns = "http://www.w3.org/2000/svg"
        original = etree.fromstring(f'<text xmlns="{svg_ns}" id="test">Content</text>')
        cloned = clone_element(original)
        self.assertEqual(original.get("id"), cloned.get("id"))
        self.assertIsNot(original, cloned)

    def test_svg_structure_exception_formatting(self):
        """Test SvgStructureException message formatting."""
        exc = SvgStructureException("test-code", extra="Extra info")
        self.assertEqual(exc.code, "test-code")
        self.assertIn("test-code", str(exc))
        self.assertIn("Extra info", str(exc))


class TestInjectorFunctions(unittest.TestCase):
    """Tests for injection-related functions."""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        for file in self.test_dir.glob('*'):
            file.unlink()
        self.test_dir.rmdir()

    def test_load_all_mappings_single_json(self):
        """Test loading single mapping file."""
        mapping_file = self.test_dir / "mapping.json"
        test_mapping = {"new": {"hello": {"ar": "مرحبا"}}}
        with open(mapping_file, 'w', encoding='utf-8') as f:
            json.dump(test_mapping, f, ensure_ascii=False)
        result = load_all_mappings([mapping_file])
        self.assertIn("new", result)

    def test_load_all_mappings_multiple_files_merge(self):
        """Test loading and merging multiple mapping files."""
        m1 = self.test_dir / "m1.json"
        m2 = self.test_dir / "m2.json"
        with open(m1, 'w') as f:
            json.dump({"key1": {"val": 1}}, f)
        with open(m2, 'w') as f:
            json.dump({"key2": {"val": 2}}, f)
        result = load_all_mappings([m1, m2])
        self.assertIn("key1", result)
        self.assertIn("key2", result)

    def test_load_all_mappings_nonexistent_returns_empty(self):
        """Test loading nonexistent file returns empty dict."""
        result = load_all_mappings([self.test_dir / "none.json"])
        self.assertEqual(result, {})

    def test_generate_unique_id_no_collision(self):
        """Test unique ID generation without collision."""
        result = generate_unique_id("text", "ar", {"other"})
        self.assertEqual(result, "text-ar")

    def test_generate_unique_id_with_collision(self):
        """Test unique ID generation handles collisions."""
        existing = {"text-ar", "text-ar-1"}
        result = generate_unique_id("text", "ar", existing)
        self.assertEqual(result, "text-ar-2")


class TestWorkflowFunctions(unittest.TestCase):
    """Tests for high-level workflow functions."""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        for file in self.test_dir.rglob('*'):
            if file.is_file():
                file.unlink()
        for d in sorted(self.test_dir.rglob('*'), reverse=True):
            if d.is_dir():
                d.rmdir()
        if self.test_dir.exists():
            self.test_dir.rmdir()

    def test_svg_extract_and_injects_basic_workflow(self):
        """Test basic svg_extract_and_injects workflow."""
        target = self.test_dir / "target.svg"
        content = '''<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><switch><text id="t1"><tspan>Hi</tspan></text></switch></svg>'''
        target.write_text(content, encoding='utf-8')
        translations = {"new": {"hi": {"ar": "مرحبا"}}}
        tree, stats = svg_extract_and_injects(translations, target, return_stats=True)
        self.assertIsNotNone(tree)
        self.assertIsNotNone(stats)


class TestExtractorEdgeCases(unittest.TestCase):
    """Edge case tests for extraction."""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        for file in self.test_dir.glob('*'):
            file.unlink()
        self.test_dir.rmdir()

    def test_extract_multiple_languages(self):
        """Test extracting with multiple language translations."""
        svg = self.test_dir / "test.svg"
        content = '''<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><switch>
<text id="t-ar" systemLanguage="ar"><tspan id="s-ar">مرحبا</tspan></text>
<text id="t-fr" systemLanguage="fr"><tspan id="s-fr">Bonjour</tspan></text>
<text id="t"><tspan id="s">Hello</tspan></text></switch></svg>'''
        svg.write_text(content, encoding='utf-8')
        result = extract(svg)
        self.assertIsNotNone(result)
        self.assertIn("new", result)

    def test_extract_empty_svg_gracefully(self):
        """Test extract handles empty SVG gracefully."""
        svg = self.test_dir / "empty.svg"
        svg.write_text('<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"></svg>', encoding='utf-8')
        result = extract(svg)
        self.assertIsNotNone(result)


class TestInjectionEdgeCases(unittest.TestCase):
    """Edge case tests for injection."""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        for file in self.test_dir.glob('*'):
            file.unlink()
        self.test_dir.rmdir()

    def test_inject_with_output_directory(self):
        """Test inject saves to specified output directory."""
        svg = self.test_dir / "test.svg"
        out_dir = self.test_dir / "out"
        out_dir.mkdir()
        content = '''<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><switch><text id="t"><tspan>Hi</tspan></text></switch></svg>'''
        svg.write_text(content, encoding='utf-8')
        mappings = {"new": {"hi": {"ar": "مرحبا"}}}
        tree = inject(svg, all_mappings=mappings, output_dir=out_dir, save_result=True)
        self.assertIsNotNone(tree)
        self.assertTrue((out_dir / "test.svg").exists())

    def test_inject_case_sensitive_mode(self):
        """Test inject in case-sensitive mode."""
        svg = self.test_dir / "test.svg"
        content = '''<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><switch><text id="t"><tspan>Hello</tspan></text></switch></svg>'''
        svg.write_text(content, encoding='utf-8')
        mappings = {"new": {"Hello": {"ar": "مرحبا"}}}
        tree, _stats = inject(svg, all_mappings=mappings, case_insensitive=False, return_stats=True)
        self.assertIsNotNone(tree)


if __name__ == '__main__':
    unittest.main()