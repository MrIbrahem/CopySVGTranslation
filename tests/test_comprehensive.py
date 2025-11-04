#

"""
Comprehensive pytest tests for CopySVGTranslation covering edge cases and additional functionality.
"""

import json
import sys
import tempfile
import shutil
from pathlib import Path
import pytest
from lxml import etree

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from CopySVGTranslation import inject, normalize_text, generate_unique_id, start_injects
from CopySVGTranslation.injection.injector import load_all_mappings
from CopySVGTranslation.injection.preparation import (
    normalize_lang,
    get_text_content,
    clone_element,
    make_translation_ready,
)
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

class TestTextUtils:
    """Test cases for text utility functions."""

    def test_normalize_text_with_tabs_and_newlines(self):
        """Test normalization with tabs and newlines."""
        assert normalize_text("hello\t\nworld") == "hello world"
        assert normalize_text("  hello\n\n  world  ") == "hello world"

    def test_normalize_text_case_insensitive(self):
        """Test case-insensitive normalization."""
        assert normalize_text("Hello World", case_insensitive=True) == "hello world"
        assert normalize_text("HELLO WORLD", case_insensitive=True) == "hello world"
        assert normalize_text("HeLLo WoRLd", case_insensitive=True) == "hello world"

    def test_normalize_text_unicode(self):
        """Test normalization with Unicode characters."""
        assert normalize_text("  مرحبا  بك  ") == "مرحبا بك"
        assert normalize_text("  你好  世界  ") == "你好 世界"


# -------------------------------
# Preparation tests
# -------------------------------

class TestPreparation:
    """Test cases for SVG preparation functions."""

    def test_normalize_lang_simple(self):
        """Test normalizing simple language codes."""
        assert normalize_lang("en") == "en"
        assert normalize_lang("AR") == "ar"
        assert normalize_lang("FR") == "fr"

    def test_normalize_lang_with_region(self):
        """Test normalizing language codes with regions."""
        assert normalize_lang("en_US") == "en-US"
        assert normalize_lang("en-GB") == "en-GB"
        assert normalize_lang("zh_CN") == "zh-CN"

    def test_normalize_lang_complex(self):
        """Test normalizing complex language codes."""
        assert normalize_lang("en_US_POSIX") == "en-US-Posix"
        assert normalize_lang("sr_Latn_RS") == "sr-Latn-RS"

    def test_normalize_lang_empty(self):
        """Test normalizing empty language code."""
        assert normalize_lang("") == ""
        assert normalize_lang(None) is None

    def test_get_text_content(self):
        """Test getting text content from elements."""
        svg_ns = "http://www.w3.org/2000/svg"
        element = etree.fromstring(
            f'''<text xmlns="{svg_ns}">Hello <tspan>World</tspan> Test</text>'''
        )
        result = get_text_content(element)
        assert "Hello" in result
        assert "World" in result

    def test_clone_element(self):
        """Test cloning an element."""
        svg_ns = "http://www.w3.org/2000/svg"
        original = etree.fromstring(f'<text xmlns="{svg_ns}" id="test">Content</text>')
        cloned = clone_element(original)
        assert original.get("id") == cloned.get("id")
        assert original.text == cloned.text
        assert original is not cloned

    def test_svg_structure_exception(self):
        """Test SvgStructureException creation."""
        exc = SvgStructureException("test-code", extra="Extra info")
        assert exc.code == "test-code"
        assert exc.extra == "Extra info"
        assert "test-code" in str(exc)
        assert "Extra info" in str(exc)

    def test_make_translation_ready_nonexistent_file(self):
        """Test make_translation_ready with nonexistent file."""
        with pytest.raises(FileNotFoundError):
            make_translation_ready(Path("/nonexistent/file.svg"))

    def test_make_translation_ready_with_valid_svg(self, temp_dir):
        """Test make_translation_ready with valid SVG."""
        svg_path = temp_dir / "test.svg"
        svg_content = '''<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><switch><text id="t1"><tspan>Hello</tspan></text></switch></svg>'''
        svg_path.write_text(svg_content, encoding='utf-8')
        tree, root = make_translation_ready(svg_path)
        assert tree is not None
        assert root is not None


# -------------------------------
# Injector tests
# -------------------------------

class TestInjector:
    """Test cases for injection functions."""

    def test_load_all_mappings_single_file(self, temp_dir):
        """Test loading a single mapping file."""
        mapping_file = temp_dir / "mapping.json"
        test_mapping = {"new": {"hello": {"ar": "مرحبا"}}}
        mapping_file.write_text(json.dumps(test_mapping, ensure_ascii=False), encoding='utf-8')
        result = load_all_mappings([mapping_file])
        assert "new" in result
        assert result["new"]["hello"]["ar"] == "مرحبا"

    def test_load_all_mappings_multiple_files(self, temp_dir):
        """Test loading multiple mapping files."""
        m1 = temp_dir / "m1.json"
        m2 = temp_dir / "m2.json"
        m1.write_text(json.dumps({"key1": {"value": 1}}), encoding='utf-8')
        m2.write_text(json.dumps({"key2": {"value": 2}}), encoding='utf-8')
        result = load_all_mappings([m1, m2])
        assert "key1" in result
        assert "key2" in result

    def test_load_all_mappings_nonexistent_file(self, temp_dir):
        """Test loading with nonexistent file."""
        result = load_all_mappings([temp_dir / "nonexistent.json"])
        assert result == {}

    def test_load_all_mappings_invalid_json(self, temp_dir):
        """Test loading with invalid JSON."""
        invalid_file = temp_dir / "invalid.json"
        invalid_file.write_text("{ invalid json", encoding='utf-8')
        result = load_all_mappings([invalid_file])
        assert result == {}

    def test_load_all_mappings_merge_behavior(self, temp_dir):
        """Test that mappings are merged correctly."""
        m1 = temp_dir / "m1.json"
        m2 = temp_dir / "m2.json"
        m1.write_text(json.dumps({"key": {"lang1": "value1"}}), encoding='utf-8')
        m2.write_text(json.dumps({"key": {"lang2": "value2"}}), encoding='utf-8')
        result = load_all_mappings([m1, m2])
        assert "lang1" in result["key"]
        assert "lang2" in result["key"]

    def test_generate_unique_id_empty_base(self):
        """Test unique ID generation with empty base ID."""
        result = generate_unique_id("", "ar", set())
        assert result == "-ar"

    def test_generate_unique_id_with_special_characters(self):
        """Test unique ID generation with special characters in base."""
        result = generate_unique_id("text-123", "fr", set())
        assert result == "text-123-fr"

    def test_inject_with_all_mappings_parameter(self, temp_dir):
        """Test inject using all_mappings parameter instead of mapping_files."""
        svg_path = temp_dir / "test.svg"
        svg_content = '''<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><switch><text id="text1"><tspan>Hello</tspan></text></switch></svg>'''
        svg_path.write_text(svg_content, encoding='utf-8')
        mappings = {"new": {"hello": {"ar": "مرحبا"}}}
        tree, stats = inject(svg_path, all_mappings=mappings, return_stats=True)
        assert tree is not None
        assert stats is not None

    def test_inject_with_output_dir(self, temp_dir):
        """Test inject with output_dir parameter."""
        svg_path = temp_dir / "test.svg"
        out_dir = temp_dir / "out"
        out_dir.mkdir()
        svg_content = '''<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><switch><text id="t"><tspan>Hello</tspan></text></switch></svg>'''
        svg_path.write_text(svg_content, encoding='utf-8')
        mappings = {"new": {"hello": {"ar": "مرحبا"}}}
        tree = inject(svg_path, all_mappings=mappings, output_dir=out_dir, save_result=True)
        assert tree is not None
        assert (out_dir / "test.svg").exists()

    def test_inject_case_sensitive(self, temp_dir):
        """Test inject with case_insensitive=False."""
        svg_path = temp_dir / "test.svg"
        svg_content = '''<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><switch><text id="t"><tspan>Hello</tspan></text></switch></svg>'''
        svg_path.write_text(svg_content, encoding='utf-8')
        mappings = {"new": {"Hello": {"ar": "مرحبا"}}}
        tree, stats = inject(svg_path, all_mappings=mappings, case_insensitive=False, return_stats=True)
        assert tree is not None
        assert stats["inserted_translations"] == 1


# -------------------------------
# Batch tests
# -------------------------------

class TestBatch:
    """Test cases for batch processing functions."""

    def test_start_injects_single_file(self, temp_dir):
        """Test batch injection with a single file."""
        svg_file = temp_dir / "test.svg"
        out_dir = temp_dir / "out"
        out_dir.mkdir()
        svg_content = '''<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><switch><text id="t"><tspan>Hello</tspan></text></switch></svg>'''
        svg_file.write_text(svg_content, encoding='utf-8')
        translations = {"new": {"hello": {"ar": "مرحبا"}}}
        result = start_injects([svg_file], translations, out_dir, overwrite=False)
        assert result["success"] == 1
        assert result["failed"] == 0

    def test_start_injects_multiple_files(self, temp_dir):
        """Test batch injection with multiple files."""
        svg1 = temp_dir / "test1.svg"
        svg2 = temp_dir / "test2.svg"
        out_dir = temp_dir / "out"
        out_dir.mkdir()
        svg_content = '''<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><switch><text id="t"><tspan>Hello</tspan></text></switch></svg>'''
        svg1.write_text(svg_content, encoding='utf-8')
        svg2.write_text(svg_content, encoding='utf-8')
        translations = {"new": {"hello": {"ar": "مرحبا"}}}
        result = start_injects([svg1, svg2], translations, out_dir)
        assert result["success"] == 2
        assert "test1.svg" in result["files"]
        assert "test2.svg" in result["files"]

    def test_start_injects_with_nonexistent_file(self, temp_dir):
        """Test batch injection with nonexistent file."""
        out_dir = temp_dir / "out"
        out_dir.mkdir()
        translations = {"new": {"hello": {"ar": "مرحبا"}}}
        result = start_injects([temp_dir / "nonexistent.svg"], translations, out_dir)
        assert result["success"] == 0
        assert result["failed"] == 1


# -------------------------------
# Edge case tests
# -------------------------------

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_normalize_text_with_only_whitespace(self):
        """Test normalization with only whitespace."""
        assert normalize_text("   ") == ""
        assert normalize_text("\n\t  ") == ""

    def test_generate_unique_id_with_many_collisions(self):
        """Test unique ID generation with many existing IDs."""
        existing = {f"id-ar-{i}" for i in range(100)}
        existing.add("id-ar")
        result = generate_unique_id("id", "ar", existing)
        assert result == "id-ar-100"

    def test_inject_with_empty_mappings(self, temp_dir):
        """Test injection with empty mappings."""
        svg = temp_dir / "test.svg"
        svg.write_text('<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><text>Test</text></svg>', encoding='utf-8')
        result = inject(svg, all_mappings={})
        assert result is None

    def test_inject_return_stats_false(self, temp_dir):
        """Test inject with return_stats=False."""
        svg = temp_dir / "test.svg"
        svg.write_text('<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><switch><text id="t"><tspan>Hello</tspan></text></switch></svg>', encoding='utf-8')
        mappings = {"new": {"hello": {"ar": "مرحبا"}}}
        result = inject(svg, all_mappings=mappings, return_stats=False)
        assert result is not None
        assert isinstance(result, etree._ElementTree)
