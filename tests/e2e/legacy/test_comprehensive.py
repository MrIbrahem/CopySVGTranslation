#

"""
Comprehensive pytest tests for CopySVGTranslation covering edge cases and additional functionality.
"""

from lxml import etree

from CopySVGTranslation.legacy import (
    inject_file_and_save,
    inject_file_tree,
)


class TestInjector:
    """Test cases for injection functions."""

    def test_inject_with_all_mappings_parameter(self, temp_dir):
        """Test inject using mapping parameter."""
        svg_path = temp_dir / "test.svg"
        svg_content = """<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><switch><text id="text1"><tspan>Hello</tspan></text></switch></svg>"""
        svg_path.write_text(svg_content, encoding="utf-8")
        mappings = {"new": {"hello": {"ar": "مرحبا"}}}
        tree, stats = inject_file_tree(
            inject_file=svg_path,
            mapping=mappings,
            return_stats=True,
        )
        assert tree is not None
        assert stats is not None

    def test_inject_with_save_path(self, temp_dir):
        """Test inject with save_path parameter."""
        svg_path = temp_dir / "test.svg"
        out_dir = temp_dir / "out"
        out_dir.mkdir()
        svg_content = """<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><switch><text id="t"><tspan>Hello</tspan></text></switch></svg>"""
        svg_path.write_text(svg_content, encoding="utf-8")
        mappings = {"new": {"hello": {"ar": "مرحبا"}}}
        tree = inject_file_and_save(
            inject_file=svg_path,
            mapping=mappings,
            save_path=out_dir / "test.svg",
        )
        assert tree is not None
        assert (out_dir / "test.svg").exists()

    def test_inject_case_sensitive(self, temp_dir):
        """Test inject with case_insensitive=False."""
        svg_path = temp_dir / "test.svg"
        svg_content = """<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><switch><text id="t"><tspan>Hello</tspan></text></switch></svg>"""
        svg_path.write_text(svg_content, encoding="utf-8")
        mappings = {"new": {"Hello": {"ar": "مرحبا"}}}
        tree, stats = inject_file_tree(
            inject_file=svg_path,
            mapping=mappings,
            case_insensitive=False,
            return_stats=True,
        )
        assert tree is not None
        assert stats["inserted_translations"] == 1

        assert stats == {
            "all_languages": 1,
            "new_languages": 1,
            "processed_switches": 1,
            "inserted_translations": 1,
            "skipped_translations": 0,
            "updated_translations": 0,
            "languages_before": [],
            "languages_after": ["ar"],
            "error": "",
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
        result = inject_file_tree(
            inject_file=svg,
            mapping={},
        )
        assert result is None

    def test_inject_return_stats_false(self, temp_dir):
        """Test inject with return_stats=False."""
        svg = temp_dir / "test.svg"
        svg.write_text(
            '<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><switch><text id="t"><tspan>Hello</tspan></text></switch></svg>',
            encoding="utf-8",
        )
        mappings = {"new": {"hello": {"ar": "مرحبا"}}}
        result = inject_file_tree(
            inject_file=svg,
            mapping=mappings,
            return_stats=False,
        )
        assert result is not None
        assert isinstance(result, etree._ElementTree)
