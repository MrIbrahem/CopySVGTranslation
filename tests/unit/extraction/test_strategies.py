"""
Unit tests for CopySVGTranslation/extraction/strategies.py module.

Classes to test: SegmentMatch, ByTspanIdStrategy, ByPositionStrategy, CompositeMatchingStrategy
"""

from __future__ import annotations

from lxml import etree

from CopySVGTranslation.core.text_node import TextNode
from CopySVGTranslation.extraction.strategies import (
    ByPositionStrategy,
    ByTspanIdStrategy,
    CompositeMatchingStrategy,
    SegmentMatch,
)

SVG_NS = "http://www.w3.org/2000/svg"


def _make_text_node(
    segments: list[tuple[str, str | None]],
    lang: str | None = None,
) -> TextNode:
    """
    Build a TextNode with tspan children.
    Each segment is (text, id).
    """
    text_elem = etree.Element(f"{{{SVG_NS}}}text")
    if lang:
        text_elem.set("systemLanguage", lang)
    for text, tid in segments:
        ts = etree.SubElement(text_elem, f"{{{SVG_NS}}}tspan")
        ts.text = text
        if tid:
            ts.set("id", tid)
    return TextNode(text_elem)


# ---------------------------------------------------------------------------
# SegmentMatch
# ---------------------------------------------------------------------------
class TestSegmentMatch:
    """Tests for the SegmentMatch dataclass."""

    def test_basic_creation(self):
        m = SegmentMatch(default_text="Hello", translated_text="مرحبا")
        assert m.default_text == "Hello"
        assert m.translated_text == "مرحبا"
        assert m.default_id is None
        assert m.translated_id is None

    def test_with_ids(self):
        m = SegmentMatch(
            default_text="Hello",
            translated_text="مرحبا",
            default_id="t0",
            translated_id="t0-ar",
        )
        assert m.default_id == "t0"
        assert m.translated_id == "t0-ar"


# ---------------------------------------------------------------------------
# ByTspanIdStrategy
# ---------------------------------------------------------------------------
class TestByTspanIdStrategy:
    """Tests for the ByTspanIdStrategy matching strategy."""

    def test_matches_by_base_id(self):
        default = _make_text_node([("Hello", "t0"), ("World", "t1")])
        translated = _make_text_node([("مرحبا", "t0-ar"), ("عالم", "t1-ar")], lang="ar")
        strategy = ByTspanIdStrategy()
        matches = strategy.match(default, translated)
        assert len(matches) == 2
        assert matches[0].translated_text == "مرحبا"
        assert matches[1].translated_text == "عالم"

    def test_matches_by_underscore_suffix(self):
        default = _make_text_node([("Hello", "t0")])
        translated = _make_text_node([("مرحبا", "t0_ar")], lang="ar")
        strategy = ByTspanIdStrategy()
        matches = strategy.match(default, translated)
        assert len(matches) == 1

    def test_no_match_when_ids_differ(self):
        default = _make_text_node([("Hello", "t0")])
        translated = _make_text_node([("مرحبا", "x99-ar")], lang="ar")
        strategy = ByTspanIdStrategy()
        matches = strategy.match(default, translated)
        assert len(matches) == 0

    def test_skips_empty_text(self):
        default = _make_text_node([("Hello", "t0")])
        translated = _make_text_node([("", "t0-ar")], lang="ar")
        strategy = ByTspanIdStrategy()
        matches = strategy.match(default, translated)
        assert len(matches) == 0

    def test_skips_missing_id(self):
        default = _make_text_node([("Hello", "t0")])
        translated = _make_text_node([("مرحبا", None)], lang="ar")
        strategy = ByTspanIdStrategy()
        matches = strategy.match(default, translated)
        assert len(matches) == 0

    def test_case_insensitive(self):
        default = _make_text_node([("Hello", "t0")])
        translated = _make_text_node([("مرحبا", "t0-ar")], lang="ar")
        strategy = ByTspanIdStrategy()
        matches = strategy.match(default, translated, case_insensitive=True)
        assert len(matches) == 1
        assert matches[0].default_text == "hello"  # lowercased

    def test_case_sensitive(self):
        default = _make_text_node([("Hello", "t0")])
        translated = _make_text_node([("مرحبا", "t0-ar")], lang="ar")
        strategy = ByTspanIdStrategy()
        matches = strategy.match(default, translated, case_insensitive=False)
        assert len(matches) == 1
        assert matches[0].default_text == "Hello"  # original case

    def test_default_node_empty_tspan(self):
        """Default tspan with empty text should be skipped."""
        default = _make_text_node([("", "t0"), ("World", "t1")])
        translated = _make_text_node([("", "t0-ar"), ("عالم", "t1-ar")], lang="ar")
        strategy = ByTspanIdStrategy()
        matches = strategy.match(default, translated)
        assert len(matches) == 1
        assert matches[0].default_text == "world" or matches[0].default_text == "World"

    def test_preserves_ids_in_match(self):
        default = _make_text_node([("Hello", "t0")])
        translated = _make_text_node([("مرحبا", "t0-ar")], lang="ar")
        strategy = ByTspanIdStrategy()
        matches = strategy.match(default, translated)
        assert matches[0].default_id == "t0"
        assert matches[0].translated_id == "t0-ar"


# ---------------------------------------------------------------------------
# ByPositionStrategy
# ---------------------------------------------------------------------------
class TestByPositionStrategy:
    """Tests for the ByPositionStrategy matching strategy."""

    def test_matches_by_index(self):
        default = _make_text_node([("Hello", "t0"), ("World", "t1")])
        translated = _make_text_node([("مرحبا", "x0"), ("عالم", "x1")], lang="ar")
        strategy = ByPositionStrategy()
        matches = strategy.match(default, translated)
        assert len(matches) == 2
        assert matches[0].translated_text == "مرحبا"
        assert matches[1].translated_text == "عالم"

    def test_fewer_translated_segments(self):
        default = _make_text_node([("Hello", "t0"), ("World", "t1")])
        translated = _make_text_node([("مرحبا", "x0")], lang="ar")
        strategy = ByPositionStrategy()
        matches = strategy.match(default, translated)
        assert len(matches) == 1

    def test_more_translated_segments(self):
        default = _make_text_node([("Hello", "t0")])
        translated = _make_text_node([("مرحبا", "x0"), ("عالم", "x1")], lang="ar")
        strategy = ByPositionStrategy()
        matches = strategy.match(default, translated)
        assert len(matches) == 1  # only matches up to default count

    def test_empty_translated_no_tspans(self):
        # Build a text node with no tspans — just bare element text
        elem = etree.Element(f"{{{SVG_NS}}}text")
        elem.set("systemLanguage", "ar")
        translated = TextNode(elem)
        default = _make_text_node([("Hello", "t0")])
        strategy = ByPositionStrategy()
        matches = strategy.match(default, translated)
        # Bare element with no text produces [""]; default has ["Hello"] → 1 match
        assert len(matches) == 1
        assert matches[0].translated_text == ""

    def test_empty_default_no_tspans(self):
        # Build a default text node with no tspans and no text
        elem = etree.Element(f"{{{SVG_NS}}}text")
        default = TextNode(elem)
        translated = _make_text_node([("مرحبا", "x0")], lang="ar")
        strategy = ByPositionStrategy()
        matches = strategy.match(default, translated)
        # Default produces [""]; translated has ["مرحبا"] → 1 match
        assert len(matches) == 1
        assert matches[0].default_text == ""

    def test_case_insensitive_default(self):
        default = _make_text_node([("Hello", "t0")])
        translated = _make_text_node([("مرحبا", "x0")], lang="ar")
        strategy = ByPositionStrategy()
        matches = strategy.match(default, translated, case_insensitive=True)
        assert matches[0].default_text == "hello"

    def test_case_sensitive_default(self):
        default = _make_text_node([("Hello", "t0")])
        translated = _make_text_node([("مرحبا", "x0")], lang="ar")
        strategy = ByPositionStrategy()
        matches = strategy.match(default, translated, case_insensitive=False)
        assert matches[0].default_text == "Hello"


# ---------------------------------------------------------------------------
# CompositeMatchingStrategy
# ---------------------------------------------------------------------------
class TestCompositeMatchingStrategy:
    """Tests for the CompositeMatchingStrategy."""

    def test_uses_first_strategy_with_results(self):
        default = _make_text_node([("Hello", "t0")])
        translated = _make_text_node([("مرحبا", "t0-ar")], lang="ar")
        composite = CompositeMatchingStrategy()
        matches = composite.match(default, translated)
        # ByTspanIdStrategy should find the match
        assert len(matches) == 1
        assert matches[0].translated_text == "مرحبا"

    def test_falls_back_to_position(self):
        # IDs don't match, so ByTspanId returns empty → falls back to ByPosition
        default = _make_text_node([("Hello", "t0")])
        translated = _make_text_node([("مرحبا", "zzz")], lang="ar")
        composite = CompositeMatchingStrategy()
        matches = composite.match(default, translated)
        assert len(matches) == 1
        assert matches[0].translated_text == "مرحبا"

    def test_empty_when_both_nodes_empty(self):
        # Both nodes produce one empty segment, so ByPosition matches them
        default_elem = etree.Element(f"{{{SVG_NS}}}text")
        translated_elem = etree.Element(f"{{{SVG_NS}}}text")
        translated_elem.set("systemLanguage", "ar")
        default = TextNode(default_elem)
        translated = TextNode(translated_elem)
        composite = CompositeMatchingStrategy()
        matches = composite.match(default, translated)
        # ByPosition produces a match of empty→empty
        assert len(matches) == 1

    def test_custom_strategies_list(self):
        # Use only ByPosition
        composite = CompositeMatchingStrategy(strategies=[ByPositionStrategy()])
        default = _make_text_node([("Hello", "t0")])
        translated = _make_text_node([("مرحبا", "zzz")], lang="ar")
        matches = composite.match(default, translated)
        assert len(matches) == 1

    def test_empty_strategies_list_uses_defaults(self):
        # Empty list is falsy, so CompositeMatchingStrategy uses defaults
        composite = CompositeMatchingStrategy(strategies=[])
        default = _make_text_node([("Hello", "t0")])
        translated = _make_text_node([("مرحبا", "t0-ar")], lang="ar")
        matches = composite.match(default, translated)
        # Falls back to default pipeline (ByTspanId → ByPosition)
        assert len(matches) >= 1
