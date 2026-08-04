"""
Extended comprehensive unit tests for CopySVGTranslation covering additional edge cases
and previously untested functions.
"""

from CopySVGTranslation.utils.text import (
    normalize_lang,
    normalize_text,
)


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
        assert normalize_text("Hello, World!") == "Hello, World!"
        assert normalize_text("  Hello,  World!  ") == "Hello, World!"

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


class TestNormalizeLang:
    """Test suite for normalize_lang function."""

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
        assert normalize_lang("en-US") == "en-US"
        assert normalize_lang("en_us") == "en-US"
        assert normalize_lang("pt_br") == "pt-BR"
        assert normalize_lang("zh-cn") == "zh-CN"

    def test_normalize_lang_complex(self):
        """Test normalizing complex language codes."""
        assert normalize_lang("en_US_POSIX") == "en-US-Posix"
        assert normalize_lang("sr_Latn_RS") == "sr-Latn-RS"

    def test_normalize_lang_empty(self):
        """Test normalizing empty language code."""
        assert normalize_lang("") == ""
        assert normalize_lang(None) is None

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

    def test_normalize_lang_simple_code(self):
        """Test normalization of simple language code."""
        assert normalize_lang("EN") == "en"
        assert normalize_lang("FR") == "fr"
        assert normalize_lang("ar") == "ar"

    def test_normalize_lang_complex_format(self):
        """Test normalization with complex format."""
        assert normalize_lang("en-us-variant") == "en-US-Variant"

    def test_normalize_lang_empty_string(self):
        """Test normalization of empty string."""
        assert normalize_lang("") == ""

    def test_normalize_lang_with_whitespace(self):
        """Test normalization handles whitespace."""
        assert normalize_lang("  en-US  ") == "en-US"
        assert normalize_lang("en us") == "en-US"

    def test_normalize_lang_hyphen_variations(self):
        """Test different hyphen/underscore variations."""
        assert normalize_lang("en-GB") == "en-GB"
        assert normalize_lang("en_GB") == "en-GB"
