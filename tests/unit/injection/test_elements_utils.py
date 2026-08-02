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

from CopySVGTranslation.injection.elements_utils import (
    extract_root_languages,
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
