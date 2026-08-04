"""
Unit tests for CopySVGTranslation/core/text_node.py module.

Classes to test: TextNode
"""

from __future__ import annotations

import pytest
from lxml import etree

from CopySVGTranslation.core.text_node import TextNode

SVG_NS = "http://www.w3.org/2000/svg"


def _make_text(
    segments: list[str] | None = None,
    *,
    text_id: str | None = "t0",
    lang: str | None = None,
    use_tspans: bool = True,
) -> TextNode:
    """Build a TextNode from text segments."""
    elem = etree.Element(f"{{{SVG_NS}}}text")
    if text_id:
        elem.set("id", text_id)
    if lang:
        elem.set("systemLanguage", lang)
    if use_tspans and segments:
        for i, seg in enumerate(segments):
            ts = etree.SubElement(elem, f"{{{SVG_NS}}}tspan")
            ts.set("id", f"{text_id}-ts{i}")
            ts.text = seg
    elif segments:
        elem.text = segments[0] if segments else ""
    return TextNode(elem)


# ---------------------------------------------------------------------------
# Identity & language
# ---------------------------------------------------------------------------
class TestTextNodeIdentity:
    """Tests for TextNode identity properties."""

    def test_id_property(self):
        node = _make_text(["Hello"], text_id="abc")
        assert node.id == "abc"

    def test_id_setter(self):
        node = _make_text(["Hello"], text_id="old")
        node.id = "new"
        assert node.id == "new"
        assert node.element.get("id") == "new"

    def test_language_property(self):
        node = _make_text(["Hello"], lang="ar")
        assert node.language == "ar"

    def test_language_none_for_fallback(self):
        node = _make_text(["Hello"])
        assert node.language is None

    def test_language_setter(self):
        node = _make_text(["Hello"])
        node.language = "fr"
        assert node.language == "fr"
        assert node.element.get("systemLanguage") == "fr"

    def test_language_setter_none_removes(self):
        node = _make_text(["Hello"], lang="ar")
        node.language = None
        assert node.language is None
        assert "systemLanguage" not in node.element.attrib

    def test_is_fallback_true(self):
        node = _make_text(["Hello"])
        assert node.is_fallback is True

    def test_is_fallback_false(self):
        node = _make_text(["Hello"], lang="ar")
        assert node.is_fallback is False


# ---------------------------------------------------------------------------
# Text content
# ---------------------------------------------------------------------------
class TestTextNodeContent:
    """Tests for TextNode text content methods."""

    def test_texts_with_tspans(self):
        node = _make_text(["Hello", "World"])
        result = node.texts(normalize=False)
        assert result == ["Hello", "World"]

    def test_texts_without_tspans(self):
        node = _make_text(["Plain text"], use_tspans=False)
        result = node.texts(normalize=False)
        assert result == ["Plain text"]

    def test_texts_normalized(self):
        node = _make_text(["  Hello   World  "])
        result = node.texts(normalize=True)
        assert result == ["Hello World"]

    def test_texts_case_insensitive(self):
        node = _make_text(["Hello World"])
        result = node.texts(normalize=True, case_insensitive=True)
        assert result == ["hello world"]

    def test_texts_empty_tspan(self):
        node = _make_text([""])
        result = node.texts(normalize=False)
        assert result == [""]

    def test_set_texts_with_tspans(self):
        node = _make_text(["Old1", "Old2"])
        node.set_texts(["New1", "New2"])
        tspans = node.tspans()
        assert tspans[0].text == "New1"
        assert tspans[1].text == "New2"

    def test_set_texts_fewer_than_tspans(self):
        node = _make_text(["A", "B", "C"])
        node.set_texts(["X"])
        tspans = node.tspans()
        assert tspans[0].text == "X"
        assert tspans[1].text == ""
        assert tspans[2].text == ""

    def test_set_texts_without_tspans(self):
        node = _make_text(["Old"], use_tspans=False)
        node.set_texts(["New"])
        assert node.element.text == "New"

    def test_set_texts_empty_list(self):
        node = _make_text(["Old"], use_tspans=False)
        node.set_texts([])
        assert node.element.text == ""


# ---------------------------------------------------------------------------
# Tspans
# ---------------------------------------------------------------------------
class TestTextNodeTspans:
    """Tests for TextNode tspan access methods."""

    def test_tspans_returns_elements(self):
        node = _make_text(["A", "B"])
        tspans = node.tspans()
        assert len(tspans) == 2
        assert isinstance(tspans[0], etree._Element)

    def test_tspans_empty_when_no_children(self):
        node = _make_text(["text"], use_tspans=False)
        tspans = node.tspans()
        assert tspans == []

    def test_iter_tspan_nodes(self):
        node = _make_text(["A", "B"])
        nodes = list(node.iter_tspan_nodes())
        assert len(nodes) == 2
        assert all(isinstance(n, TextNode) for n in nodes)


# ---------------------------------------------------------------------------
# Cloning
# ---------------------------------------------------------------------------
class TestTextNodeClone:
    """Tests for TextNode cloning."""

    def test_clone_creates_new_element(self):
        node = _make_text(["Hello"], text_id="orig")
        cloned = node.clone()
        assert cloned.element is not node.element

    def test_clone_preserves_text(self):
        node = _make_text(["Hello", "World"])
        cloned = node.clone()
        assert cloned.texts(normalize=False) == ["Hello", "World"]

    def test_clone_preserves_attributes(self):
        node = _make_text(["Hello"], text_id="orig", lang="ar")
        cloned = node.clone()
        assert cloned.id == "orig"
        assert cloned.language == "ar"

    def test_clone_is_independent(self):
        node = _make_text(["Hello"])
        cloned = node.clone()
        cloned.set_texts(["Changed"])
        # Original should be unchanged
        assert node.texts(normalize=False) == ["Hello"]
