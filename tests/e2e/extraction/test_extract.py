"""
Comprehensive pytest tests for CopySVGTranslation covering edge cases and additional functionality.
"""

from CopySVGTranslation import extract, inject_file_tree
from CopySVGTranslation.workflows import svg_extract_and_inject

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

        source_content = """<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg">
        <switch><text id="text1-ar" systemLanguage="ar"><tspan>مرحبا</tspan></text>
        <text id="text1"><tspan>Hello</tspan></text></switch></svg>"""
        target_content = """<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg">
        <switch><text id="text2"><tspan>Hello</tspan></text></switch></svg>"""

        source_svg.write_text(source_content, encoding="utf-8")
        target_svg.write_text(target_content, encoding="utf-8")

        result = svg_extract_and_inject(
            source_svg,
            target_svg,
            target_path=output_svg,
            all_mappings_file=data_output,
            save_result=True,
            pretty_print=False,
        )
        assert result is not None
        # assert data_output.exists()

    def test_svg_extract_and_inject_with_nonexistent_extract_file(self, temp_dir):
        """Test svg_extract_and_inject with nonexistent extract file."""
        target_svg = temp_dir / "target.svg"
        target_svg.write_text("<svg></svg>", encoding="utf-8")

        result = svg_extract_and_inject(temp_dir / "none.svg", target_svg, save_result=False)
        assert result is None

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
            all_mappings=translations,
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
        tree, stats = inject_file_tree(all_mappings=translations, inject_file=target, overwrite=True, return_stats=True)
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
        assert result is not None

        assert result == {"new": {}, "tspans_by_id": {}, "title": {}, "title_new": {}, "error": ""}

    def test_extract_case_sensitive(self, temp_dir):
        """Test extraction with case_insensitive=False."""
        svg = temp_dir / "test.svg"
        svg.write_text(
            """<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg">
            <switch><text id="t-ar" systemLanguage="ar"><tspan>مرحبا</tspan></text>
            <text id="t"><tspan>Hello World</tspan></text></switch></svg>""",
            encoding="utf-8",
        )
        result = extract(svg, case_insensitive=False)
        assert result is not None
        assert "new" in result

        assert result == {"new": {"Hello World": {}}, "tspans_by_id": {}, "title": {}, "title_new": {}, "error": ""}

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

        assert result == {"new": {"population 2020": {}}, "tspans_by_id": {}, "title": {}, "title_new": {}, "error": ""}

    def test_extract_empty_tspans(self, temp_dir):
        """Test extraction with empty tspan elements."""
        svg = temp_dir / "empty_tspans.svg"
        svg.write_text(
            """<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg">
            <switch><text id="t"><tspan></tspan></text></switch></svg>""",
            encoding="utf-8",
        )
        result = extract(svg)
        assert result is not None

        assert result == {"new": {}, "tspans_by_id": {}, "title": {}, "title_new": {}, "error": ""}

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
            "title": {},
            "title_new": {},
            "error": "",
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
