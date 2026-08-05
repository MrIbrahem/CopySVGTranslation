"""
Comprehensive pytest tests for CopySVGTranslation covering edge cases and additional functionality.
"""

from CopySVGTranslation.legacy.extract import extract
from CopySVGTranslation.legacy.inject import inject_file_tree

# -------------------------------
# Workflows tests
# -------------------------------


class TestWorkflows:
    """Test cases for workflow functions."""

    def test_inject_with_return_stats(self, temp_dir):
        """Test inject with return_stats=True."""
        target = temp_dir / "target.svg"
        target.write_text(
            """<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg">
            <switch><text id="text1"><tspan>Hello</tspan></text></switch></svg>""",
            encoding="utf-8",
        )
        translations = {"new": {"hello": {"ar": "مرحبا"}}}
        tree, stats = inject_file_tree(
            mapping=translations,
            inject_file=target,
            save_result=False,
            return_stats=True,
        )
        assert tree is not None
        assert stats is not None
        assert "processed_switches" in stats

    def test_inject_with_overwrite(self, temp_dir):
        """Test inject with overwrite parameter."""
        target = temp_dir / "target.svg"
        target.write_text(
            """<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg">
            <switch><text id="text1-ar" systemLanguage="ar"><tspan>Old</tspan></text>
            <text id="text1"><tspan>Hello</tspan></text></switch></svg>""",
            encoding="utf-8",
        )
        translations = {"new": {"hello": {"ar": "New"}}}
        tree, stats = inject_file_tree(
            mapping=translations,
            inject_file=target,
            overwrite=True,
            return_stats=True,
        )
        assert tree is not None
        assert stats.get("updated_translations", 0) > 0


# -------------------------------
# Extractor tests
# -------------------------------


class TestExtractor:
    """Test cases for extraction functions."""

    def test_extract_with_no_switches(self, temp_dir):
        """Test extraction with SVG containing no switch elements."""
        svg = temp_dir / "no_switch.svg"
        svg.write_text(
            """<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><text>Just text</text></svg>""",
            encoding="utf-8",
        )
        result = extract(svg)
        assert result is None

    def test_extract_case_sensitive(self, temp_dir):
        """Test extraction with case_insensitive=False."""
        svg = temp_dir / "test.svg"
        svg.write_text(
            """<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg">
            <switch><text id="t-ar" systemLanguage="ar"><tspan>مرحبا</tspan></text>
            <text id="t"><tspan>Hello World</tspan></text></switch></svg>""",
            encoding="utf-8",
        )
        result = extract(
            svg,
            case_insensitive=False,
        )
        assert result is not None
        assert "new" in result

        assert result == {"new": {"Hello World": {}}, "tspans_by_id": {}, "title_new": {}, "meta": {}, "error": ""}

    def test_extract_with_year_suffix(self, temp_dir):
        """Test extraction with year suffixes in text."""
        svg = temp_dir / "year.svg"
        svg.write_text(
            """<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg">
            <switch><text id="t-ar" systemLanguage="ar"><tspan>السكان 2020</tspan></text>
            <text id="t"><tspan>Population 2020</tspan></text></switch></svg>""",
            encoding="utf-8",
        )
        result = extract(svg)
        assert result is not None

        assert result == {"new": {"population 2020": {}}, "tspans_by_id": {}, "title_new": {}, "meta": {}, "error": ""}

    def test_extract_empty_tspans(self, temp_dir):
        """Test extraction with empty tspan elements."""
        svg = temp_dir / "empty_tspans.svg"
        svg.write_text(
            """<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg">
            <switch><text id="t"><tspan></tspan></text></switch></svg>""",
            encoding="utf-8",
        )
        result = extract(svg)
        assert result is None

    def test_extract_translation_tspan_without_id(self, temp_dir):
        """Translations without IDs should fall back to positional matching."""
        svg = temp_dir / "missing_id.svg"
        svg.write_text(
            """<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg">
            <switch><text><tspan id="greeting">Hello</tspan></text>
            <text systemLanguage="es" id="greeting-es"><tspan>Hola</tspan></text></switch></svg>""",
            encoding="utf-8",
        )
        result = extract(svg)
        assert result is not None
        assert "new" in result
        assert "hello" in result["new"]
        assert result["new"]["hello"].get("es") in (None, "Hola")

        assert result == {
            "new": {"hello": {}},
            "tspans_by_id": {"greeting": "Hello"},
            "title_new": {},
            "error": "",
            "meta": {},
        }


# -------------------------------
# Edge case tests
# -------------------------------


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_extract_with_malformed_xml(self, temp_dir):
        """Test extraction with malformed XML."""
        svg = temp_dir / "bad.svg"
        svg.write_text("<svg><text>Unclosed", encoding="utf-8")
        result = extract(svg)
        assert result is None
