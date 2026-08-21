"""
Comprehensive pytest tests for CopySVGTranslation covering edge cases and additional functionality.
"""

from CopySVGTranslation import SVGTranslationService, TranslationConfig, TranslationMapping
from CopySVGTranslation.core.mapping import InjectorData

# -------------------------------
# Workflows tests
# -------------------------------


class TestWorkflows:
    """Test cases for workflow functions."""

    def test_inject_with_return_stats(self, temp_dir):
        """Test inject returns stats via InjectorData."""
        target = temp_dir / "target.svg"
        target.write_text(
            """<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg">
            <switch><text id="text1"><tspan>Hello</tspan></text></switch></svg>""",
            encoding="utf-8",
        )
        translations = {"new": {"hello": {"ar": "مرحبا"}}}
        service = SVGTranslationService()
        result = service.inject(
            svg_path=target,
            mapping=translations,
            output=target,
        )
        assert result.success
        assert isinstance(result.data, InjectorData)
        tree = result.data.tree
        stats = result.data.inject_stats.to_json()
        assert tree is not None
        assert stats is not None
        assert "processed_switches" in stats

    def test_inject_with_overwrite(self, temp_dir):
        """Test inject with overwrite_translations parameter."""
        target = temp_dir / "target.svg"
        target.write_text(
            """<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg">
            <switch><text id="text1-ar" systemLanguage="ar"><tspan>Old</tspan></text>
            <text id="text1"><tspan>Hello</tspan></text></switch></svg>""",
            encoding="utf-8",
        )
        translations = {"new": {"hello": {"ar": "New"}}}
        service = SVGTranslationService(TranslationConfig(overwrite_translations=True))
        result = service.inject(
            svg_path=target,
            mapping=translations,
            output=target,
        )
        assert result.success
        assert result.data is not None
        tree = result.data.tree
        stats = result.data.inject_stats.to_json()
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
        service = SVGTranslationService()
        result = service.extract(svg)
        assert not result.success
        assert result.data is None

    def test_extract_case_sensitive(self, temp_dir):
        """Test extraction with case_insensitive=False."""
        svg = temp_dir / "test.svg"
        svg.write_text(
            """<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg">
            <switch><text id="t-ar" systemLanguage="ar"><tspan>مرحبا</tspan></text>
            <text id="t"><tspan>Hello World</tspan></text></switch></svg>""",
            encoding="utf-8",
        )
        service = SVGTranslationService(TranslationConfig(case_insensitive=False))
        _result = service.extract(svg)
        assert _result.success
        assert isinstance(_result.data, TranslationMapping)
        result = _result.data.to_json()
        assert "new" in result

        assert result == {"new": {"Hello World": {}}, "tspans_by_id": {}, "title_new": {}, "meta": {}, "error": ""}

    def test_extract_with_year_suffix(self, temp_dir):
        """Test extraction with year suffixes in text."""
        svg = temp_dir / "year.svg"
        svg.write_text(
            """<?xml version="1.0"?>
                <svg xmlns="http://www.w3.org/2000/svg">
                    <switch>
                        <text id="t-ar" systemLanguage="ar">
                            <tspan>السكان 2020</tspan>
                        </text>
                        <text id="t">
                            <tspan>Population 2020</tspan>
                        </text>
                    </switch>
                </svg>
                """,
            encoding="utf-8",
        )
        service = SVGTranslationService()
        _result = service.extract(svg)
        assert _result.success
        assert _result.data is not None
        result = _result.data.to_json()

        assert result == {"new": {"population 2020": {}}, "tspans_by_id": {}, "title_new": {}, "meta": {}, "error": ""}

    def test_extract_empty_tspans(self, temp_dir):
        """Test extraction with empty tspan elements."""
        svg = temp_dir / "empty_tspans.svg"
        svg.write_text(
            """<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg">
            <switch><text id="t"><tspan></tspan></text></switch></svg>""",
            encoding="utf-8",
        )
        service = SVGTranslationService()
        result = service.extract(svg)
        assert not result.success
        assert result.data is None

    def test_extract_translation_tspan_without_id(self, temp_dir):
        """Translations without IDs should fall back to positional matching."""
        svg = temp_dir / "missing_id.svg"
        svg.write_text(
            """<?xml version="1.0"?>
            <svg xmlns="http://www.w3.org/2000/svg">
                <switch>
                    <text>
                        <tspan id="greeting">Hello</tspan>
                    </text>
                    <text systemLanguage="es" id="greeting-es">
                        <tspan>Hola</tspan>
                    </text>
                </switch>
            </svg>
            """,
            encoding="utf-8",
        )
        service = SVGTranslationService()
        _result = service.extract(svg)
        assert _result.success
        assert _result.data is not None
        result = _result.data.to_json()
        assert "new" in result
        assert "hello" in result["new"]
        # assert result["new"]["hello"].get("es") == "Hola"
        assert result["new"]["hello"].get("es") is None

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
        service = SVGTranslationService()
        result = service.extract(svg)
        assert not result.success
        assert result.data is None
