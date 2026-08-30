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

        assert sorted(extract_root_languages(root)) == ["en", "fr"]


class TestExtractRootLanguages:
    """Tests for extract_root_languages function."""

    def test_extract_root_languages(self): ...


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


class TestSvgTag:
    """Tests for svg_tag function."""

    def test_svg_tag_clark_notation(self):
        assert svg_tag("text") == "{http://www.w3.org/2000/svg}text"

    def test_svg_tag_various_names(self):
        assert svg_tag("switch") == "{http://www.w3.org/2000/svg}switch"
        assert svg_tag("tspan") == "{http://www.w3.org/2000/svg}tspan"


class TestLocalName:
    """Tests for local_name function."""

    def test_local_name_with_namespace(self):
        svg_content = '<svg xmlns="http://www.w3.org/2000/svg"><text>Hi</text></svg>'
        root = etree.fromstring(svg_content)
        text = root.find(".//{http://www.w3.org/2000/svg}text")
        assert local_name(text) == "text"

    def test_local_name_without_namespace(self):
        root = etree.fromstring("<foo><bar>Hi</bar></foo>")
        bar = root.find("bar")
        assert local_name(bar) == "bar"

    def test_local_name_non_string_tag(self):
        # Comments and processing instructions have non-string tags
        # (a callable), which str() renders rather than raising.
        comment = etree.Comment("note")
        assert local_name(comment) == str(comment.tag)


class TestIsSvgElement:
    """Tests for is_svg_element function."""

    def test_is_svg_element_namespaced_match(self):
        root = etree.fromstring('<svg xmlns="http://www.w3.org/2000/svg"><text>Hi</text></svg>')
        text = root.find(".//{http://www.w3.org/2000/svg}text")
        assert is_svg_element(text, "text") is True
        assert is_svg_element(text, "switch") is False

    def test_is_svg_element_no_namespace_match(self):
        root = etree.fromstring("<root><text>Hi</text></root>")
        text = root.find("text")
        assert is_svg_element(text, "text") is True

    def test_is_svg_element_no_match(self):
        root = etree.fromstring('<svg xmlns="http://www.w3.org/2000/svg"><g>X</g></svg>')
        g = root.find(".//{http://www.w3.org/2000/svg}g")
        assert is_svg_element(g, "text") is False


class TestFindallSvg:
    """Tests for findall_svg function."""

    def test_findall_svg_finds_descendants(self):
        svg_content = """<svg xmlns="http://www.w3.org/2000/svg">
            <text systemLanguage="en">A</text>
            <g>
                <text systemLanguage="fr">B</text>
            </g>
        </svg>"""
        root = etree.fromstring(svg_content)
        texts = findall_svg(root, "text")
        assert len(texts) == 2
        assert all(is_svg_element(t, "text") for t in texts)

    def test_findall_svg_no_match(self):
        root = etree.fromstring('<svg xmlns="http://www.w3.org/2000/svg"><g>X</g></svg>')
        assert findall_svg(root, "text") == []

    def test_findall_svg_only_within_svg_namespace(self):
        svg_content = """<svg xmlns="http://www.w3.org/2000/svg">
            <foo:text xmlns:foo="http://example.com/foo">Nope</foo:text>
            <text>Yep</text>
        </svg>"""
        root = etree.fromstring(svg_content)
        texts = findall_svg(root, "text")
        assert len(texts) == 1
        assert local_name(texts[0]) == "text"


class TestXpathSvg:
    """Tests for xpath_svg function."""

    def test_xpath_svg_returns_matches(self):
        svg_content = """<svg xmlns="http://www.w3.org/2000/svg">
            <text systemLanguage="en">A</text>
            <text systemLanguage="fr">B</text>
        </svg>"""
        root = etree.fromstring(svg_content)
        result = xpath_svg(root, ".//svg:text")
        assert len(result) == 2

    def test_xpath_svg_with_predicate(self):
        svg_content = """<svg xmlns="http://www.w3.org/2000/svg">
            <text systemLanguage="en">A</text>
            <text>B</text>
        </svg>"""
        root = etree.fromstring(svg_content)
        result = xpath_svg(root, ".//svg:text[@systemLanguage]")
        assert len(result) == 1
        assert local_name(result[0]) == "text"


class TestCollectIds:
    """Tests for collect_ids function."""

    def test_collect_ids_finds_all(self):
        svg_content = """<svg xmlns="http://www.w3.org/2000/svg">
            <text id="t1">A</text>
            <text id="t2">B</text>
            <g id="g1"><text id="t3">C</text></g>
        </svg>"""
        root = etree.fromstring(svg_content)
        ids = collect_ids(root)
        assert ids == {"t1", "t2", "g1", "t3"}

    def test_collect_ids_empty(self):
        root = etree.fromstring('<svg xmlns="http://www.w3.org/2000/svg"><text>A</text></svg>')
        assert collect_ids(root) == set()

    def test_collect_ids_skips_empty_id(self):
        svg_content = '<svg xmlns="http://www.w3.org/2000/svg"><text id="">A</text><g id="g1"/></svg>'
        root = etree.fromstring(svg_content)
        assert collect_ids(root) == {"g1"}


class TestSortSwitchChildren:
    """Tests for sort_switch_children function."""

    def _switch(self, content: str):
        svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg">
            <switch>
                {content}
            </switch>
        </svg>"""
        root = etree.fromstring(svg_content)
        return root, root.find(".//{http://www.w3.org/2000/svg}switch")

    def test_sort_switch_children_fallback_last(self):
        root, switch = self._switch(
            """<text id="trsvg1" systemLanguage="ar">Arabic</text>
               <text>Default</text>
               <text id="trsvg2" systemLanguage="fr">French</text>"""
        )
        sort_switch_children(switch)
        order = [t.get("systemLanguage") for t in switch if is_svg_element(t, "text")]
        # Fallback (None) should be last.
        assert order[-1] is None
        assert order[:2] == ["ar", "fr"]

    def test_sort_switch_children_sorts_by_trsvg_number(self):
        root, switch = self._switch(
            """<text id="trsvg3" systemLanguage="ar">Arabic</text>
               <text id="trsvg1" systemLanguage="fr">French</text>
               <text id="trsvg2" systemLanguage="en">English</text>"""
        )
        sort_switch_children(switch)
        order = [t.get("id") for t in switch if is_svg_element(t, "text")]
        assert order == ["trsvg1", "trsvg2", "trsvg3"]

    def test_sort_switch_children_put_fallback_first(self):
        root, switch = self._switch(
            """<text id="trsvg1" systemLanguage="ar">Arabic</text>
               <text>Default</text>"""
        )
        sort_switch_children(switch, put_fallback_last=False)
        order = [t.get("systemLanguage") for t in switch if is_svg_element(t, "text")]
        assert order[0] is None
        assert order[-1] == "ar"

    def test_sort_switch_children_leaves_non_text_untouched(self):
        root, switch = self._switch(
            """<text id="trsvg2" systemLanguage="fr">French</text>
               <metadata>keep</metadata>
               <text id="trsvg1" systemLanguage="ar">Arabic</text>"""
        )
        sort_switch_children(switch)
        # Non-text child positions relative to text reordering stay valid;
        # just ensure metadata still present and texts sorted.
        tags = [local_name(c) for c in switch]
        assert "metadata" in tags
        order = [t.get("systemLanguage") for t in switch if is_svg_element(t, "text")]
        assert order == ["ar", "fr"]

    def test_sort_switch_children_idempotent(self):
        root, switch = self._switch(
            """<text id="trsvg2" systemLanguage="fr">French</text>
               <text>Default</text>
               <text id="trsvg1" systemLanguage="ar">Arabic</text>"""
        )
        sort_switch_children(switch)
        snapshot = [etree.tostring(t) for t in switch if is_svg_element(t, "text")]
        sort_switch_children(switch)
        second = [etree.tostring(t) for t in switch if is_svg_element(t, "text")]
        assert snapshot == second


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
            """<text systemLanguage="ar">Arabic</text><text systemLanguage="fr">French</text><text>Default</text>"""
        )
        assert is_switch_sorted(switch) is True
        assert are_switches_sorted(switch) is True

    def test_is_switch_sorted_when_fallback_first(self):
        _, switch = self._switch("""<text>Default</text><text systemLanguage="ar">Arabic</text>""")
        assert is_switch_sorted(switch) is False

    def test_is_switch_sorted_when_lang_after_fallback(self):
        _, switch = self._switch(
            """<text>Default</text><text systemLanguage="fr">French</text><text systemLanguage="ar">Arabic</text>"""
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
