# ruff: noqa: F401
"""
Unit tests for CopySVGTranslation/injection/xml.py module.

TODO: write tests
"""

import shutil
import tempfile
import textwrap
from pathlib import Path

import pytest
from lxml import etree

from CopySVGTranslation.utils.xml import (
    are_switches_sorted,
    collect_ids,
    extract_root_languages,
    findall_svg,
    is_svg_element,
    is_switch_sorted,
    local_name,
    sort_switch_children,
    sort_switch_texts,
    svg_tag,
    tree_languages,
    xpath_svg,
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

        assert sorted(tree_languages(tree)) == ["en", "fr"]
        assert sorted(extract_root_languages(root)) == ["en", "fr"]


class TestExtractRootLanguages:
    """Tests for extract_root_languages function."""

    def test_extract_root_languages(self): ...


class TestTreeLangs:
    """Tests for tree_languages function."""

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


class TestSwitchSorted(TestSetup):
    """Test suite for is_switch_sorted / are_switches_sorted functions."""

    def _switch(self, content: str):
        svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg">
            <switch>
                {content}
            </switch>
        </svg>"""
        root = etree.fromstring(svg_content)
        return root, root.find(".//{http://www.w3.org/2000/svg}switch")

    def test_is_switch_sorted_when_sorted(self):
        _, switch = self._switch(
            '<text systemLanguage="ar">Arabic</text>'
            '<text systemLanguage="fr">French</text>'
            '<text>Default</text>'
        )
        assert is_switch_sorted(switch) is True
        assert are_switches_sorted(switch) is True

    def test_is_switch_sorted_when_fallback_first(self):
        _, switch = self._switch(
            '<text>Default</text>'
            '<text systemLanguage="ar">Arabic</text>'
        )
        assert is_switch_sorted(switch) is False

    def test_is_switch_sorted_when_lang_after_fallback(self):
        _, switch = self._switch(
            '<text>Default</text>'
            '<text systemLanguage="fr">French</text>'
            '<text systemLanguage="ar">Arabic</text>'
        )
        assert is_switch_sorted(switch) is False

    def test_are_switches_sorted_empty_tree(self):
        root = etree.fromstring('<svg xmlns="http://www.w3.org/2000/svg"></svg>')
        assert are_switches_sorted(root) is True

    def test_are_switches_sorted_multiple_switches(self):
        svg_content = """<svg xmlns="http://www.w3.org/2000/svg">
            <switch>
                <text>Default</text>
                <text systemLanguage="ar">Arabic</text>
            </switch>
            <switch>
                <text systemLanguage="fr">French</text>
                <text>Default</text>
            </switch>
        </svg>"""
        root = etree.fromstring(svg_content)
        # First switch is unsorted, so the whole tree is unsorted.
        assert are_switches_sorted(root) is False

    def test_none_inputs_return_true(self):
        assert are_switches_sorted(None) is True
        assert is_switch_sorted(None) is True
