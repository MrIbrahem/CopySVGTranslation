"""
Unit tests for CopySVGTranslation/injection/elements_utils.py module.


TODO: write tests
"""

import shutil
import tempfile
import textwrap
from pathlib import Path

import pytest
from lxml import etree

from CopySVGTranslation.utils.elements_utils import (
    extract_root_languages,
    extract_text_from_node,
    file_langs,
    sort_switch_texts,
    tree_langs,
)


class TestSetup:
    @pytest.fixture(autouse=True)
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.svg_path = self.test_dir / "source.svg"
        self.svg_path.write_text("<svg></svg>", encoding="utf-8")

        yield
        """Clean up test fixtures."""
        # Clean up temporary files
        shutil.rmtree(self.test_dir)


def write_svg(tmp_path: Path, content: str) -> Path:
    svg_path = tmp_path / "sample.svg"
    svg_path.write_text(textwrap.dedent(content), encoding="utf-8")
    return svg_path


class TestElementsUtils:
    def test_file_langs_handles_element_root(self):
        svg = textwrap.dedent(
            """
            <svg xmlns=\"http://www.w3.org/2000/svg\">
                <text systemLanguage=\"en\">Hello</text>
                <text systemLanguage=\"fr\">Bonjour</text>
            </svg>
            """
        )

        root = etree.fromstring(svg)
        tree = etree.ElementTree(root)

        assert sorted(tree_langs(tree)) == ["en", "fr"]
        assert sorted(extract_root_languages(root)) == ["en", "fr"]


class TestExtractRootLanguages:
    """Tests for extract_root_languages function."""

    def test_extract_root_languages(self): ...


class TestFileLangs:
    """Tests for file_langs function."""

    def test_file_langs(self): ...

    def test_inject_tracks_new_languages(self, tmp_path):
        svg_path = write_svg(
            tmp_path,
            """
            <svg xmlns=\"http://www.w3.org/2000/svg\">
                <switch>
                    <text id=\"t1\"><tspan>Hello</tspan></text>
                </switch>
            </svg>
            """,
        )

        before_languages = file_langs(svg_path)

        assert before_languages == set()


class TestTreeLangs:
    """Tests for tree_langs function."""

    def test_tree_langs(self): ...


class TestSortSwitchTexts(TestSetup):
    """Test suite for sort_switch_texts function."""

    def test_sort_switch_texts_basic(self):
        """Test sorting text elements in a switch."""
        svg_content = """<svg xmlns="http://www.w3.org/2000/svg">
            <switch>
                <text systemLanguage="ar">Arabic</text>
                <text>Default</text>
                <text systemLanguage="fr">French</text>
            </switch>
        </svg>"""
        root = etree.fromstring(svg_content)
        switch = root.find(".//{http://www.w3.org/2000/svg}switch")
        assert switch is not None

        sort_switch_texts(switch)

        texts = switch.findall(".//{http://www.w3.org/2000/svg}text")
        # Default (no systemLanguage) should be last
        assert texts[-1].get("systemLanguage") is None

    def test_sort_switch_texts_empty_switch(self):
        """Test sorting an empty switch element."""
        svg_content = '<svg xmlns="http://www.w3.org/2000/svg"><switch></switch></svg>'
        root = etree.fromstring(svg_content)
        switch = root.find(".//{http://www.w3.org/2000/svg}switch")
        assert switch is not None

        # Should not raise an error
        sort_switch_texts(switch)

    def test_sort_switch_texts_only_default(self):
        """Test sorting with only default text."""
        svg_content = """<svg xmlns="http://www.w3.org/2000/svg">
            <switch>
                <text>Default only</text>
            </switch>
        </svg>"""
        root = etree.fromstring(svg_content)
        switch = root.find(".//{http://www.w3.org/2000/svg}switch")
        assert switch is not None

        sort_switch_texts(switch)

        texts = switch.findall(".//{http://www.w3.org/2000/svg}text")
        assert len(texts) == 1


class TestTextUtils:
    """Test cases for text utility functions."""

    def test_extract_text_from_node_with_tspans(self):
        """Test extracting text from a node with tspans."""
        svg_ns = "http://www.w3.org/2000/svg"
        text_node = etree.fromstring(f"""<text xmlns="{svg_ns}"><tspan>Hello</tspan><tspan>World</tspan></text>""")
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
        text_node = etree.fromstring(f"""<text xmlns="{svg_ns}"><tspan>   </tspan><tspan>Text</tspan></text>""")
        result = extract_text_from_node(text_node)
        assert result == ["", "Text"]


class TestExtractTextFromNode:
    """Test suite for extract_text_from_node function."""

    def test_extract_from_text_with_tspans(self):
        """Test extraction from text element with tspan children."""
        xml = """<text xmlns="http://www.w3.org/2000/svg">
            <tspan>First</tspan>
            <tspan>Second</tspan>
        </text>"""
        node = etree.fromstring(xml)
        result = extract_text_from_node(node)

        assert result == ["First", "Second"]

    def test_extract_from_text_without_tspans(self):
        """Test extraction from text element without tspans."""
        xml = '<text xmlns="http://www.w3.org/2000/svg">Direct text</text>'
        node = etree.fromstring(xml)
        result = extract_text_from_node(node)

        assert result == ["Direct text"]

    def test_extract_from_text_with_empty_tspans(self):
        """Test extraction with empty tspan elements."""
        xml = """<text xmlns="http://www.w3.org/2000/svg">
            <tspan></tspan>
            <tspan>Content</tspan>
        </text>"""
        node = etree.fromstring(xml)
        result = extract_text_from_node(node)

        assert result == ["", "Content"]

    def test_extract_from_text_with_whitespace_tspans(self):
        """Test extraction handles whitespace in tspans."""
        xml = """<text xmlns="http://www.w3.org/2000/svg">
            <tspan>  Spaces  </tspan>
            <tspan>	Tabs	</tspan>
        </text>"""
        node = etree.fromstring(xml)
        result = extract_text_from_node(node)

        assert result == ["Spaces", "Tabs"]

    def test_extract_from_empty_text_node(self):
        """Test extraction from empty text node."""
        xml = '<text xmlns="http://www.w3.org/2000/svg"></text>'
        node = etree.fromstring(xml)
        result = extract_text_from_node(node)

        assert result == [""]

    def test_extract_with_unicode_content(self):
        """Test extraction with Unicode content."""
        xml = """<text xmlns="http://www.w3.org/2000/svg">
            <tspan>مرحبا</tspan>
            <tspan>你好</tspan>
            <tspan>Привет</tspan>
        </text>"""
        node = etree.fromstring(xml)
        result = extract_text_from_node(node)

        assert result == ["مرحبا", "你好", "Привет"]

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
