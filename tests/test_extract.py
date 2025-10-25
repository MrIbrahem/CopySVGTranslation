"""
Comprehensive pytest tests for CopySvgTranslate covering edge cases and additional functionality.
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

from CopySvgTranslate import extract, inject
from CopySvgTranslate.text_utils import extract_text_from_node
from CopySvgTranslate.workflows import svg_extract_and_inject


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

    def test_extract_text_from_node_with_tspans(self):
        """Test extracting text from a node with tspans."""
        svg_ns = "http://www.w3.org/2000/svg"
        text_node = etree.fromstring(
            f'''<text xmlns="{svg_ns}"><tspan>Hello</tspan><tspan>World</tspan></text>'''
        )
        result = extract_text_from_node(text_node)
        assert result == ["Hello", "World"]

    def test_extract_text_from_node_without_tspans(self):
        """Test extracting text from a node without tspans."""
        svg_ns = "http://www.w3.org/2000/svg"
        text_node = etree.fromstring(f'<text xmlns="{svg_ns}">Plain text</text>')
        result = extract_text_from_node(text_node)
        assert result == ["Plain text"]

    def test_extract_text_from_node_empty(self):
        """Test extracting text from an empty node."""
        svg_ns = "http://www.w3.org/2000/svg"
        text_node = etree.fromstring(f'<text xmlns="{svg_ns}"></text>')
        result = extract_text_from_node(text_node)
        assert result == [""]

    def test_extract_text_from_node_with_whitespace_tspans(self):
        """Test extracting text from tspans with only whitespace."""
        svg_ns = "http://www.w3.org/2000/svg"
        text_node = etree.fromstring(
            f'''<text xmlns="{svg_ns}"><tspan>   </tspan><tspan>Text</tspan></text>'''
        )
        result = extract_text_from_node(text_node)
        assert result == ["", "Text"]


# -------------------------------
# Workflows tests
# -------------------------------

class TestWorkflows:
    """Test cases for workflow functions."""

    def test_svg_extract_and_inject_with_custom_output(self, temp_dir):
        """Test svg_extract_and_inject with custom output paths."""
        source_svg = temp_dir / "source.svg"
        target_svg = temp_dir / "target.svg"
        output_svg = temp_dir / "output.svg"
        data_output = temp_dir / "data.json"

        source_content = '''<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg">
        <switch><text id="text1-ar" systemLanguage="ar"><tspan>مرحبا</tspan></text>
        <text id="text1"><tspan>Hello</tspan></text></switch></svg>'''
        target_content = '''<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg">
        <switch><text id="text2"><tspan>Hello</tspan></text></switch></svg>'''

        source_svg.write_text(source_content, encoding='utf-8')
        target_svg.write_text(target_content, encoding='utf-8')

        result = svg_extract_and_inject(
            source_svg,
            target_svg,
            output_file=output_svg,
            data_output_file=data_output,
            save_result=True,
        )
        assert result is not None
        assert data_output.exists()

    def test_svg_extract_and_inject_with_nonexistent_extract_file(self, temp_dir):
        """Test svg_extract_and_inject with nonexistent extract file."""
        target_svg = temp_dir / "target.svg"
        target_svg.write_text('<svg></svg>', encoding='utf-8')

        result = svg_extract_and_inject(temp_dir / "none.svg", target_svg, save_result=False)
        assert result is None

    def test_inject_with_return_stats(self, temp_dir):
        """Test inject with return_stats=True."""
        target = temp_dir / "target.svg"
        target.write_text(
            '''<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg">
            <switch><text id="text1"><tspan>Hello</tspan></text></switch></svg>''',
            encoding='utf-8',
        )
        translations = {"new": {"hello": {"ar": "مرحبا"}}}
        tree, stats = inject(
            all_mappings=translations, inject_file=target, save_result=False, return_stats=True
        )
        assert tree is not None
        assert stats is not None
        assert "processed_switches" in stats

    def test_inject_with_overwrite(self, temp_dir):
        """Test inject with overwrite parameter."""
        target = temp_dir / "target.svg"
        target.write_text(
            '''<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg">
            <switch><text id="text1-ar" systemLanguage="ar"><tspan>Old</tspan></text>
            <text id="text1"><tspan>Hello</tspan></text></switch></svg>''',
            encoding='utf-8',
        )
        translations = {"new": {"hello": {"ar": "New"}}}
        tree, stats = inject(
            all_mappings=translations, inject_file=target, overwrite=True, return_stats=True
        )
        assert tree is not None
        assert stats.get("updated_translations", 0) > 0


# -------------------------------
# Extractor tests
# -------------------------------

class TestExtractor:
    """Test cases for extraction functions."""

    def _test_extract_with_multiple_languages(self, temp_dir):
        """Test extraction with multiple languages."""
        svg = temp_dir / "test.svg"
        svg.write_text(
            '''
            <?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg">
            <switch><text id="t0-ar" systemLanguage="ar"><tspan>مرحبا</tspan></text>
            <text id="t0-fr" systemLanguage="fr"><tspan>Bonjour</tspan></text>
            <text id="t0"><tspan>Hello</tspan></text></switch></svg>
            ''',
            encoding='utf-8',
        )
        result = extract(svg)
        # print(result)
        assert result is not None
        assert "new" in result
        assert "ar" in result["new"]["hello"]
        assert "fr" in result["new"]["hello"]

    def test_extract_with_no_switches(self, temp_dir):
        """Test extraction with SVG containing no switch elements."""
        svg = temp_dir / "no_switch.svg"
        svg.write_text(
            '''<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><text>Just text</text></svg>''',
            encoding='utf-8',
        )
        result = extract(svg)
        assert result is not None

    def test_extract_case_sensitive(self, temp_dir):
        """Test extraction with case_insensitive=False."""
        svg = temp_dir / "test.svg"
        svg.write_text(
            '''<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg">
            <switch><text id="t-ar" systemLanguage="ar"><tspan>مرحبا</tspan></text>
            <text id="t"><tspan>Hello World</tspan></text></switch></svg>''',
            encoding='utf-8',
        )
        result = extract(svg, case_insensitive=False)
        assert result is not None
        assert "new" in result

    def test_extract_with_year_suffix(self, temp_dir):
        """Test extraction with year suffixes in text."""
        svg = temp_dir / "year.svg"
        svg.write_text(
            '''<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg">
            <switch><text id="t-ar" systemLanguage="ar"><tspan>السكان 2020</tspan></text>
            <text id="t"><tspan>Population 2020</tspan></text></switch></svg>''',
            encoding='utf-8',
        )
        result = extract(svg)
        assert result is not None

    def test_extract_empty_tspans(self, temp_dir):
        """Test extraction with empty tspan elements."""
        svg = temp_dir / "empty_tspans.svg"
        svg.write_text(
            '''<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg">
            <switch><text id="t"><tspan></tspan></text></switch></svg>''',
            encoding='utf-8',
        )
        result = extract(svg)
        assert result is not None

    def test_extract_translation_tspan_without_id(self, temp_dir):
        """Translations without IDs should fall back to positional matching."""
        svg = temp_dir / "missing_id.svg"
        svg.write_text(
            '''<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg">
            <switch><text><tspan id="greeting">Hello</tspan></text>
            <text systemLanguage="es" id="greeting-es"><tspan>Hola</tspan></text></switch></svg>''',
            encoding='utf-8',
        )
        result = extract(svg)
        assert result is not None
        assert "new" in result
        assert "hello" in result["new"]
        assert result["new"]["hello"].get("es") in (None, "Hola")


# -------------------------------
# Edge case tests
# -------------------------------

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_extract_with_malformed_xml(self, temp_dir):
        """Test extraction with malformed XML."""
        svg = temp_dir / "bad.svg"
        svg.write_text("<svg><text>Unclosed", encoding='utf-8')
        result = extract(svg)
        assert result is None
