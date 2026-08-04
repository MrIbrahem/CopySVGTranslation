"""
Unit tests for CopySVGTranslation/core/switch_node.py module.

Classes to test: SwitchNode
"""

from __future__ import annotations

from lxml import etree

from CopySVGTranslation.core.switch_node import SwitchNode
from CopySVGTranslation.core.text_node import TextNode

SVG_NS = "http://www.w3.org/2000/svg"


def _make_switch(texts: list[dict]) -> SwitchNode:
    """
    Build a SwitchNode from a list of dicts:
    [{"text": "Hello", "id": "t0", "lang": None}, ...]
    """
    switch_elem = etree.Element(f"{{{SVG_NS}}}switch")
    for t in texts:
        text_elem = etree.SubElement(switch_elem, f"{{{SVG_NS}}}text")
        if "id" in t:
            text_elem.set("id", t["id"])
        if t.get("lang"):
            text_elem.set("systemLanguage", t["lang"])
        ts = etree.SubElement(text_elem, f"{{{SVG_NS}}}tspan")
        ts.text = t.get("text", "")
        if "id" in t:
            ts.set("id", f"{t['id']}-ts")
    return SwitchNode(switch_elem)


# ---------------------------------------------------------------------------
# text_nodes
# ---------------------------------------------------------------------------
class TestSwitchNodeTextNodes:
    """Tests for SwitchNode.text_nodes."""

    def test_returns_all_text_nodes(self):
        sn = _make_switch(
            [
                {"text": "مرحبا", "id": "t0-ar", "lang": "ar"},
                {"text": "Hello", "id": "t0"},
            ]
        )
        nodes = sn.text_nodes()
        assert len(nodes) == 2
        assert all(isinstance(n, TextNode) for n in nodes)

    def test_empty_switch(self):
        sn = _make_switch([])
        assert sn.text_nodes() == []


# ---------------------------------------------------------------------------
# iter_text_nodes
# ---------------------------------------------------------------------------
class TestSwitchNodeIterTextNodes:
    """Tests for SwitchNode.iter_text_nodes."""

    def test_yields_text_nodes(self):
        sn = _make_switch(
            [
                {"text": "Hello", "id": "t0"},
                {"text": "Bonjour", "id": "t0-fr", "lang": "fr"},
            ]
        )
        nodes = list(sn.iter_text_nodes())
        assert len(nodes) == 2


# ---------------------------------------------------------------------------
# fallback / default_text_node
# ---------------------------------------------------------------------------
class TestSwitchNodeFallback:
    """Tests for SwitchNode.fallback and default_text_node."""

    def test_fallback_returns_node_without_lang(self):
        sn = _make_switch(
            [
                {"text": "مرحبا", "id": "t0-ar", "lang": "ar"},
                {"text": "Hello", "id": "t0"},
            ]
        )
        fb = sn.fallback()
        assert fb is not None
        assert fb.is_fallback
        assert fb.texts(normalize=False) == ["Hello"]

    def test_fallback_none_when_all_have_lang(self):
        sn = _make_switch(
            [
                {"text": "مرحبا", "id": "t0-ar", "lang": "ar"},
                {"text": "Bonjour", "id": "t0-fr", "lang": "fr"},
            ]
        )
        assert sn.fallback() is None

    def test_default_text_node_is_same_element_as_fallback(self):
        sn = _make_switch(
            [
                {"text": "Hello", "id": "t0"},
            ]
        )
        dt = sn.default_text_node()
        fb = sn.fallback()
        assert dt is not None and fb is not None
        assert dt.element is fb.element


# ---------------------------------------------------------------------------
# existing_languages
# ---------------------------------------------------------------------------
class TestSwitchNodeExistingLanguages:
    """Tests for SwitchNode.existing_languages."""

    def test_returns_languages(self):
        sn = _make_switch(
            [
                {"text": "مرحبا", "id": "t0-ar", "lang": "ar"},
                {"text": "Bonjour", "id": "t0-fr", "lang": "fr"},
                {"text": "Hello", "id": "t0"},
            ]
        )
        langs = sn.existing_languages()
        assert langs == {"ar", "fr"}

    def test_empty_when_no_languages(self):
        sn = _make_switch(
            [
                {"text": "Hello", "id": "t0"},
            ]
        )
        assert sn.existing_languages() == set()


# ---------------------------------------------------------------------------
# find_by_language
# ---------------------------------------------------------------------------
class TestSwitchNodeFindByLanguage:
    """Tests for SwitchNode.find_by_language."""

    def test_finds_matching_node(self):
        sn = _make_switch(
            [
                {"text": "مرحبا", "id": "t0-ar", "lang": "ar"},
                {"text": "Hello", "id": "t0"},
            ]
        )
        node = sn.find_by_language("ar")
        assert node is not None
        assert node.language == "ar"

    def test_returns_none_for_missing(self):
        sn = _make_switch(
            [
                {"text": "Hello", "id": "t0"},
            ]
        )
        assert sn.find_by_language("zh") is None


# ---------------------------------------------------------------------------
# append / remove
# ---------------------------------------------------------------------------
class TestSwitchNodeAppendRemove:
    """Tests for SwitchNode.append and remove."""

    def test_append_adds_text_node(self):
        sn = _make_switch([{"text": "Hello", "id": "t0"}])
        new_elem = etree.Element(f"{{{SVG_NS}}}text")
        new_elem.set("systemLanguage", "fr")
        ts = etree.SubElement(new_elem, f"{{{SVG_NS}}}tspan")
        ts.text = "Bonjour"
        new_node = TextNode(new_elem)

        sn.append(new_node)
        assert len(sn.text_nodes()) == 2

    def test_remove_removes_text_node(self):
        sn = _make_switch(
            [
                {"text": "Hello", "id": "t0"},
                {"text": "Bonjour", "id": "t0-fr", "lang": "fr"},
            ]
        )
        fr_node = sn.find_by_language("fr")
        assert fr_node is not None
        sn.remove(fr_node)
        assert len(sn.text_nodes()) == 1
        assert sn.find_by_language("fr") is None


# ---------------------------------------------------------------------------
# reorder
# ---------------------------------------------------------------------------
class TestSwitchNodeReorder:
    """Tests for SwitchNode.reorder."""

    def test_reorder_fallback_last(self):
        sn = _make_switch(
            [
                {"text": "Hello", "id": "t0"},
                {"text": "مرحبا", "id": "t1-ar", "lang": "ar"},
                {"text": "Bonjour", "id": "t2-fr", "lang": "fr"},
            ]
        )
        sn.reorder(put_fallback_last=True)
        nodes = sn.text_nodes()
        # Fallback should be last
        assert nodes[-1].is_fallback

    def test_reorder_fallback_first(self):
        sn = _make_switch(
            [
                {"text": "مرحبا", "id": "t1-ar", "lang": "ar"},
                {"text": "Hello", "id": "t0"},
                {"text": "Bonjour", "id": "t2-fr", "lang": "fr"},
            ]
        )
        sn.reorder(put_fallback_last=False)
        nodes = sn.text_nodes()
        assert nodes[0].is_fallback

    def test_reorder_preserves_all_nodes(self):
        sn = _make_switch(
            [
                {"text": "Hello", "id": "t0"},
                {"text": "مرحبا", "id": "t1-ar", "lang": "ar"},
                {"text": "Bonjour", "id": "t2-fr", "lang": "fr"},
            ]
        )
        sn.reorder()
        assert len(sn.text_nodes()) == 3
