"""Additional comprehensive pytest tests for CopySVGTranslation."""

import json
import sys
import tempfile
import shutil
from pathlib import Path
from lxml import etree
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from CopySVGTranslation import extract, inject, normalize_text, generate_unique_id
from CopySVGTranslation.text_utils import extract_text_from_node
from CopySVGTranslation.injection.injector import load_all_mappings
from CopySVGTranslation.injection.preparation import normalize_lang, get_text_content, clone_element
from CopySVGTranslation.injection import (
    SvgStructureException,
)

# -------------------------------
# Fixtures
# -------------------------------


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test use."""
    d = Path(tempfile.mkdtemp())
    yield d
    shutil.rmtree(d)


# -------------------------------
# Text utility tests
# -------------------------------

class TestTextUtilsComprehensive:
    """Comprehensive tests for text utility functions."""

    def test_normalize_text_tabs_newlines(self):
        """Test normalization with tabs and newlines."""
        assert normalize_text("hello\t\nworld") == "hello world"
        assert normalize_text("  hello\n\n  world  ") == "hello world"

    def test_normalize_text_case_insensitive_variations(self):
        """Test case-insensitive normalization variations."""
        assert normalize_text("Hello World", case_insensitive=True) == "hello world"
        assert normalize_text("HELLO WORLD", case_insensitive=True) == "hello world"

    def test_normalize_text_unicode_chars(self):
        """Test normalization with Unicode characters."""
        assert normalize_text("  مرحبا  بك  ") == "مرحبا بك"
        assert normalize_text("  你好  世界  ") == "你好 世界"

    def test_extract_text_from_node_with_multiple_tspans(self):
        """Test extracting text from node with multiple tspans."""
        svg_ns = "http://www.w3.org/2000/svg"
        text_node = etree.fromstring(f'<text xmlns="{svg_ns}"><tspan>Hello</tspan><tspan>World</tspan></text>')
        result = extract_text_from_node(text_node)
        assert result == ["Hello", "World"]

    def test_extract_text_from_node_plain_text(self):
        """Test extracting plain text from node without tspans."""
        svg_ns = "http://www.w3.org/2000/svg"
        text_node = etree.fromstring(f'<text xmlns="{svg_ns}">Plain text</text>')
        result = extract_text_from_node(text_node)
        assert result == ["Plain text"]


# -------------------------------
# Preparation function tests
# -------------------------------

class TestPreparationFunctions:
    """Tests for SVG preparation utility functions."""

    def test_normalize_lang_simple_codes(self):
        """Test normalizing simple language codes."""
        assert normalize_lang("en") == "en"
        assert normalize_lang("AR") == "ar"
        assert normalize_lang("FR") == "fr"

    def test_normalize_lang_with_region_codes(self):
        """Test normalizing language codes with regions."""
        assert normalize_lang("en_US") == "en-US"
        assert normalize_lang("en-GB") == "en-GB"
        assert normalize_lang("zh_CN") == "zh-CN"

    def test_normalize_lang_complex_codes(self):
        """Test normalizing complex language codes."""
        assert normalize_lang("en_US_POSIX") == "en-US-Posix"

    def test_get_text_content_with_tspans(self):
        """Test getting text content from elements with nested tspans."""
        svg_ns = "http://www.w3.org/2000/svg"
        element = etree.fromstring(f'<text xmlns="{svg_ns}">Hello <tspan>World</tspan> Test</text>')
        result = get_text_content(element)
        assert "Hello" in result
        assert "World" in result

    def test_clone_element_creates_copy(self):
        """Test element cloning creates independent copy."""
        svg_ns = "http://www.w3.org/2000/svg"
        original = etree.fromstring(f'<text xmlns="{svg_ns}" id="test">Content</text>')
        cloned = clone_element(original)
        assert original.get("id") == cloned.get("id")
        assert original is not cloned

    def test_svg_structure_exception_formatting(self):
        """Test SvgStructureException message formatting."""
        exc = SvgStructureException("test-code", extra="Extra info")
        assert exc.code == "test-code"
        assert "test-code" in str(exc)
        assert "Extra info" in str(exc)


# -------------------------------
# Injector tests
# -------------------------------

class TestInjectorFunctions:
    """Tests for injection-related functions."""

    def test_load_all_mappings_single_json(self, temp_dir):
        """Test loading single mapping file."""
        mapping_file = temp_dir / "mapping.json"
        test_mapping = {"new": {"hello": {"ar": "مرحبا"}}}
        mapping_file.write_text(json.dumps(test_mapping, ensure_ascii=False), encoding='utf-8')
        result = load_all_mappings([mapping_file])
        assert "new" in result

    def test_load_all_mappings_multiple_files_merge(self, temp_dir):
        """Test loading and merging multiple mapping files."""
        m1 = temp_dir / "m1.json"
        m2 = temp_dir / "m2.json"
        m1.write_text(json.dumps({"key1": {"val": 1}}), encoding='utf-8')
        m2.write_text(json.dumps({"key2": {"val": 2}}), encoding='utf-8')
        result = load_all_mappings([m1, m2])
        assert "key1" in result
        assert "key2" in result

    def test_load_all_mappings_nonexistent_returns_empty(self, temp_dir):
        """Test loading nonexistent file returns empty dict."""
        result = load_all_mappings([temp_dir / "none.json"])
        assert result == {}

    def test_generate_unique_id_no_collision(self):
        """Test unique ID generation without collision."""
        result = generate_unique_id("text", "ar", {"other"})
        assert result == "text-ar"

    def test_generate_unique_id_with_collision(self):
        """Test unique ID generation handles collisions."""
        existing = {"text-ar", "text-ar-1"}
        result = generate_unique_id("text", "ar", existing)
        assert result == "text-ar-2"


# -------------------------------
# Workflow tests
# -------------------------------

class TestWorkflowFunctions:
    """Tests for high-level workflow functions."""

    def test_inject_basic_workflow(self, temp_dir):
        """Test basic inject workflow."""
        target = temp_dir / "target.svg"
        content = '''<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><switch><text id="t1"><tspan>Hi</tspan></text></switch></svg>'''
        target.write_text(content, encoding='utf-8')

        translations = {"new": {"hi": {"ar": "مرحبا"}}}

        tree, stats = inject(all_mappings=translations, inject_file=target, output_dir=temp_dir, return_stats=True)

        assert tree is not None
        assert stats is not None


# -------------------------------
# Extraction edge cases
# -------------------------------

class TestExtractorEdgeCases:
    """Edge case tests for extraction."""

    def test_extract_multiple_languages(self, temp_dir):
        """Test extracting with multiple language translations."""
        svg = temp_dir / "test.svg"
        content = '''<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><switch>
<text id="t-ar" systemLanguage="ar"><tspan id="s-ar">مرحبا</tspan></text>
<text id="t-fr" systemLanguage="fr"><tspan id="s-fr">Bonjour</tspan></text>
<text id="t"><tspan id="s">Hello</tspan></text></switch></svg>'''
        svg.write_text(content, encoding='utf-8')
        result = extract(svg)
        assert result is not None
        assert "new" in result

    def test_extract_empty_svg_gracefully(self, temp_dir):
        """Test extract handles empty SVG gracefully."""
        svg = temp_dir / "empty.svg"
        svg.write_text('<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"></svg>', encoding='utf-8')
        result = extract(svg)
        assert result is not None


# -------------------------------
# Injection edge cases
# -------------------------------

class TestInjectionEdgeCases:
    """Edge case tests for injection."""

    def test_inject_with_output_directory(self, temp_dir):
        """Test inject saves to specified output directory."""
        svg = temp_dir / "test.svg"
        out_dir = temp_dir / "out"
        out_dir.mkdir()
        content = '''<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><switch><text id="t"><tspan>Hi</tspan></text></switch></svg>'''
        svg.write_text(content, encoding='utf-8')
        mappings = {"new": {"hi": {"ar": "مرحبا"}}}
        tree = inject(svg, all_mappings=mappings, output_dir=out_dir, save_result=True)
        assert tree is not None
        assert (out_dir / "test.svg").exists()

    def test_inject_case_sensitive_mode(self, temp_dir):
        """Test inject in case-sensitive mode."""
        svg = temp_dir / "test.svg"
        content = '''<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><switch><text id="t"><tspan>Hello</tspan></text></switch></svg>'''
        svg.write_text(content, encoding='utf-8')
        mappings = {"new": {"Hello": {"ar": "مرحبا"}}}
        tree, stats = inject(svg, all_mappings=mappings, case_insensitive=False, return_stats=True)
        assert tree is not None
        assert stats is not None
