"""
Extended comprehensive unit tests for CopySVGTranslation covering additional edge cases
and previously untested functions.
"""

from lxml import etree

from CopySVGTranslation.text_utils import extract_text_from_node, normalize_text


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
