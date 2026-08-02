"""
Extended comprehensive unit tests for CopySVGTranslation covering additional edge cases
and previously untested functions.
"""

import shutil
import tempfile
from pathlib import Path

import pytest

from CopySVGTranslation.injection.exceptions import (
    SvgStructureExceptionError,
)
from CopySVGTranslation.injection.preparation import (
    make_translation_ready,
)


class TestMakeTranslationReadyEdgeCases:
    """Test suite for make_translation_ready edge cases."""

    @pytest.fixture(autouse=True)
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path(tempfile.mkdtemp())

        yield
        """Clean up test fixtures."""
        # Clean up temporary files
        shutil.rmtree(self.test_dir)

    def test_make_translation_ready_with_tref(self):
        """Test that SVG with tref raises exception."""
        svg_path = self.test_dir / "test.svg"
        svg_content = """<svg xmlns="http://www.w3.org/2000/svg">
            <text><tref href="#someref"/></text>
        </svg>"""
        svg_path.write_text(svg_content, encoding="utf-8")

        with pytest.raises(SvgStructureExceptionError) as exc_info:
            make_translation_ready(svg_path)

        assert "tref" in str(exc_info.value)

    def test_make_translation_ready_with_css_ids(self):
        """Test that CSS with ID selectors raises exception."""
        svg_path = self.test_dir / "test.svg"
        svg_content = """<svg xmlns="http://www.w3.org/2000/svg">
            <style>#myid { fill: red; }</style>
            <text id="myid">Test</text>
        </svg>"""
        svg_path.write_text(svg_content, encoding="utf-8")

        with pytest.raises(SvgStructureExceptionError) as exc_info:
            make_translation_ready(svg_path)

        assert "css" in str(exc_info.value).lower()

    def test_make_translation_ready_with_dollar_sign(self):
        """Test that text with dollar signs raises exception."""
        svg_path = self.test_dir / "test.svg"
        svg_content = """<svg xmlns="http://www.w3.org/2000/svg">
            <text>Price: $10</text>
        </svg>"""
        svg_path.write_text(svg_content, encoding="utf-8")

        with pytest.raises(SvgStructureExceptionError) as exc_info:
            make_translation_ready(svg_path)

        assert "dollar" in str(exc_info.value).lower()

    def test_make_translation_ready_nested_tspans(self):
        """Test that nested tspans raise exception."""
        svg_path = self.test_dir / "test.svg"
        svg_content = """<svg xmlns="http://www.w3.org/2000/svg">
            <text><tspan>Outer<tspan>Inner</tspan></tspan></text>
        </svg>"""
        svg_path.write_text(svg_content, encoding="utf-8")

        with pytest.raises(SvgStructureExceptionError) as exc_info:
            make_translation_ready(svg_path)

        assert "nested" in str(exc_info.value).lower()

    def test_make_translation_ready_wraps_raw_text(self):
        """Test that raw text in text elements is wrapped in tspans."""
        svg_path = self.test_dir / "test.svg"
        svg_content = """<svg xmlns="http://www.w3.org/2000/svg">
            <text>Raw text content</text>
        </svg>"""
        svg_path.write_text(svg_content, encoding="utf-8")

        _tree, root = make_translation_ready(svg_path)

        text_elem = root.find(".//{http://www.w3.org/2000/svg}text")
        assert text_elem is not None
        tspans = text_elem.findall("{http://www.w3.org/2000/svg}tspan")
        assert len(tspans) > 0

    def test_make_translation_ready_creates_switch(self):
        """Test that text elements are wrapped in switch elements."""
        svg_path = self.test_dir / "test.svg"
        svg_content = """<svg xmlns="http://www.w3.org/2000/svg">
            <g><text id="t1">Content</text></g>
        </svg>"""
        svg_path.write_text(svg_content, encoding="utf-8")

        _tree, root = make_translation_ready(svg_path)

        switches = root.findall(".//{http://www.w3.org/2000/svg}switch")
        assert len(switches) > 0

    def test_make_translation_ready_assigns_ids(self):
        """Test that missing IDs are assigned."""
        svg_path = self.test_dir / "test.svg"
        svg_content = """<svg xmlns="http://www.w3.org/2000/svg">
            <text>No ID</text>
        </svg>"""
        svg_path.write_text(svg_content, encoding="utf-8")

        _tree, root = make_translation_ready(svg_path)

        text_elem = root.find(".//{http://www.w3.org/2000/svg}text")
        assert text_elem is not None
        assert text_elem.get("id") is not None

    def test_make_translation_ready_duplicate_lang_error(self):
        """Test that duplicate language codes in switch raise exception."""
        svg_path = self.test_dir / "test.svg"
        svg_content = """<svg xmlns="http://www.w3.org/2000/svg">
            <switch>
                <text systemLanguage="ar">Arabic 1</text>
                <text systemLanguage="ar">Arabic 2</text>
            </switch>
        </svg>"""
        svg_path.write_text(svg_content, encoding="utf-8")

        with pytest.raises(SvgStructureExceptionError) as exc_info:
            make_translation_ready(svg_path)

        assert "lang" in str(exc_info.value).lower()

    def test_make_translation_ready_splits_comma_langs(self):
        """Test that comma-separated languages are split."""
        svg_path = self.test_dir / "test.svg"
        svg_content = """<svg xmlns="http://www.w3.org/2000/svg">
            <switch>
                <text systemLanguage="ar,fr">Multi</text>
                <text>Default</text>
            </switch>
        </svg>"""
        svg_path.write_text(svg_content, encoding="utf-8")

        _tree, root = make_translation_ready(svg_path)

        switch = root.find(".//{http://www.w3.org/2000/svg}switch")
        assert switch is not None

        text_elems = switch.findall("{http://www.w3.org/2000/svg}text")

        # Should have split into separate text elements
        assert len(text_elems) > 2

    def test_make_translation_ready_invalid_node_id(self):
        """Test that invalid node IDs raise exception."""
        svg_path = self.test_dir / "test.svg"
        svg_content = """<svg xmlns="http://www.w3.org/2000/svg">
            <text id="invalid|id">Test</text>
        </svg>"""
        svg_path.write_text(svg_content, encoding="utf-8")

        with pytest.raises(SvgStructureExceptionError) as exc_info:
            make_translation_ready(svg_path)

        assert "id" in str(exc_info.value).lower()
