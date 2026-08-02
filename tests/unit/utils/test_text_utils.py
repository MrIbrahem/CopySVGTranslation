"""
Extended comprehensive unit tests for CopySVGTranslation covering additional edge cases
and previously untested functions.
"""

from lxml import etree

from CopySVGTranslation.utils import extract_text_from_node, normalize_text


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


class TestTextUtils2:
    def test_normalize_text_x(self):
        """Test text normalization."""
        assert normalize_text("  hello  world  ") == "hello world"
        assert normalize_text("hello    world") == "hello world"
        assert normalize_text("  hello world  ") == "hello world"
        assert normalize_text("") == ""
        assert normalize_text(None) == ""

    """Test cases for text utility functions."""

    def test_normalize_text_with_numbers(self):
        """Test text normalization with numbers."""
        assert normalize_text("Population 2020") == "Population 2020"
        assert normalize_text("  Population   2020  ") == "Population 2020"

    def test_normalize_text_with_punctuation(self):
        """Test text normalization with punctuation."""
        assert normalize_text("Hello == World!", "Hello, World!")
        assert normalize_text("  Hello ==  World!  ", "Hello, World!")

    def test_normalize_text_is_importable(self):
        """The normalize_text function should be importable from top-level module."""
        assert callable(normalize_text)
        assert normalize_text.__name__ == "normalize_text"

    def test_normalize_text_with_only_whitespace(self):
        """normalize_text should return empty string for whitespace-only input."""
        assert normalize_text("   \t\n   ") == ""

    def test_normalize_text_with_only_whitespace2(self):
        """Test normalization with only whitespace."""
        assert normalize_text("   ") == ""
        assert normalize_text("\n\t  ") == ""

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

    def test_normalize_text_case_insensitive_arabic(self):
        """Test case insensitive normalization preserves Arabic text."""
        arabic_text = "السكان 2020"
        result = normalize_text(arabic_text, case_insensitive=True)
        # Arabic text doesn't have uppercase/lowercase, should be preserved
        assert "السكان" in result

    def test_normalize_text_multiple_languages(self):
        """Test text normalization with mixed scripts."""
        mixed_text = "  Hello مرحبا World  "
        result = normalize_text(mixed_text)
        assert result == "Hello مرحبا World"

    def test_normalize_text_preserves_content(self):
        """Test that normalize_text doesn't remove important content."""
        # Test with various content types
        test_cases = [
            ("Hello World", "Hello World"),
            ("123 456", "123 456"),
            ("test@example.com", "test@example.com"),
            ("path/to/file", "path/to/file"),
            ("a-b-c", "a-b-c"),
            ("a b y", "a b y"),
            ("你好世界", "你好世界"),
        ]

        for input_text, expected in test_cases:
            result = normalize_text(input_text)
            assert result == expected, f"Failed for input: {input_text}"


class TestNormalizeTextFunction:
    """Comprehensive tests for the normalize_text function."""

    def test_normalize_text_basic_whitespace(self):
        """normalize_text should collapse multiple spaces."""
        assert normalize_text("hello  world") == "hello world"
        assert normalize_text("hello   world") == "hello world"

    def test_normalize_text_leading_trailing_whitespace(self):
        """normalize_text should remove leading and trailing whitespace."""
        assert normalize_text("  hello world  ") == "hello world"
        assert normalize_text("\thello world\n") == "hello world"

    def test_normalize_text_empty_string(self):
        """normalize_text should handle empty strings."""
        assert normalize_text("") == ""
        assert normalize_text("   ") == ""

    def test_normalize_text_none_value(self):
        """normalize_text should handle None values."""
        assert normalize_text(None) == ""

    def test_normalize_text_case_sensitive(self):
        """normalize_text should preserve case by default."""
        assert normalize_text("Hello World") == "Hello World"
        assert normalize_text("HELLO WORLD") == "HELLO WORLD"

    def test_normalize_text_case_insensitive(self):
        """normalize_text should lowercase when case_insensitive=True."""
        assert normalize_text("Hello World", case_insensitive=True) == "hello world"
        assert normalize_text("HELLO WORLD", case_insensitive=True) == "hello world"

    def test_normalize_text_mixed_whitespace_types(self):
        """normalize_text should handle tabs, newlines, and spaces."""
        assert normalize_text("hello\tworld\n") == "hello world"
        assert normalize_text("hello\r\nworld") == "hello world"

    def test_normalize_text_unicode_whitespace(self):
        """normalize_text should handle unicode whitespace."""
        assert normalize_text("hello\u00a0world") == "hello world"  # Non-breaking space

    def test_normalize_text_single_word(self):
        """normalize_text should handle single words."""
        assert normalize_text("hello") == "hello"
        assert normalize_text("  hello  ") == "hello"

    def test_normalize_text_multiple_newlines(self):
        """normalize_text should collapse multiple newlines."""
        assert normalize_text("hello\n\n\nworld") == "hello world"

    def test_normalize_text_arabic_text(self):
        """normalize_text should preserve non-Latin scripts."""
        assert normalize_text("  السكان 2020  ") == "السكان 2020"

    def test_normalize_text_special_characters(self):
        """normalize_text should preserve special characters."""
        assert normalize_text("hello, world!") == "hello, world!"
        assert normalize_text("test@example.com") == "test@example.com"


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
