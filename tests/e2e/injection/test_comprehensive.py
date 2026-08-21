#

"""
Comprehensive pytest tests for CopySVGTranslation covering edge cases and additional functionality.
"""

from lxml import etree

from CopySVGTranslation import SVGTranslationService, TranslationConfig
from CopySVGTranslation.core.mapping import InjectorData, InjectorStats


class TestInjector:
    """Test cases for injection functions."""

    def test_inject_with_all_mappings_parameter(self, temp_dir):
        """Test inject using mapping parameter."""
        svg_path = temp_dir / "test.svg"
        svg_content = """<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><switch><text id="text1"><tspan>Hello</tspan></text></switch></svg>"""
        svg_path.write_text(svg_content, encoding="utf-8")
        mappings = {"new": {"hello": {"ar": "مرحبا"}}}
        service = SVGTranslationService()
        result = service.inject(
            svg_path=svg_path,
            mapping=mappings,
            output=svg_path,
        )
        assert result.success
        assert result.data.tree is not None
        stats = result.data.inject_stats.to_json()
        assert stats is not None

    def test_inject_with_save_path(self, temp_dir):
        """Test inject with output parameter."""
        svg_path = temp_dir / "test.svg"
        out_dir = temp_dir / "out"
        out_dir.mkdir()
        svg_content = """<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><switch><text id="t"><tspan>Hello</tspan></text></switch></svg>"""
        svg_path.write_text(svg_content, encoding="utf-8")
        mappings = {"new": {"hello": {"ar": "مرحبا"}}}
        service = SVGTranslationService()
        result = service.inject(
            svg_path=svg_path,
            mapping=mappings,
            output=out_dir / "test.svg",
            save=True,
        )
        assert result.success
        assert result.data.tree is not None
        assert (out_dir / "test.svg").exists()

    def test_inject_case_sensitive(self, temp_dir):
        """Test inject with case_insensitive=False."""
        svg_path = temp_dir / "test.svg"
        svg_content = """<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><switch><text id="t"><tspan>Hello</tspan></text></switch></svg>"""
        svg_path.write_text(svg_content, encoding="utf-8")
        mappings = {"new": {"Hello": {"ar": "مرحبا"}}}

        service = SVGTranslationService(TranslationConfig(case_insensitive=False))

        result = service.inject(
            svg_path=svg_path,
            mapping=mappings,
            output=svg_path,
        )
        assert isinstance(result.data, InjectorData)
        tree = result.data.tree
        stats = result.data.inject_stats.to_json()

        assert tree is not None
        assert stats["inserted_translations"] == 1

        assert stats == {
            "all_languages_count": 1,
            "new_languages_count": 1,
            "processed_switches": 1,
            "inserted_translations": 1,
            "skipped_translations": 0,
            "updated_translations": 0,
            "languages_before": [],
            "languages_after": ["ar"],
        }


# -------------------------------
# Edge case tests
# -------------------------------


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_inject_with_empty_mappings(self, temp_dir):
        """Test injection with empty mappings."""
        svg = temp_dir / "test.svg"
        svg.write_text(
            '<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><text>Test</text></svg>', encoding="utf-8"
        )
        service = SVGTranslationService()

        result = service.inject(
            svg_path=svg,
            mapping={},
            output=svg,
        )
        assert isinstance(result.data, InjectorData)

        assert result.data.inject_stats == InjectorStats(
            all_languages_count=0,
            new_languages_count=0,
            processed_switches=0,
            inserted_translations=0,
            skipped_translations=0,
            updated_translations=0,
            languages_before=[],
            languages_after=[],
        )
        assert result.data.error.code is None

    def test_inject_return_stats_false(self, temp_dir):
        """Test inject with return_stats=False."""
        svg = temp_dir / "test.svg"
        svg.write_text(
            '<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><switch><text id="t"><tspan>Hello</tspan></text></switch></svg>',
            encoding="utf-8",
        )
        mappings = {"new": {"hello": {"ar": "مرحبا"}}}
        service = SVGTranslationService()

        result = service.inject(
            svg_path=svg,
            mapping=mappings,
            output=svg,
        )
        assert isinstance(result.data, InjectorData)
        assert result is not None
        assert isinstance(result.data.tree, etree._ElementTree)
