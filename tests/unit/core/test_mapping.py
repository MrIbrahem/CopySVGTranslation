"""
Unit tests for CopySVGTranslation/core/mapping.py module.

Classes to test: TranslationEntry, TranslationMapping
"""

from __future__ import annotations

import pytest

from CopySVGTranslation.core.mapping import TranslationEntry, TranslationMapping


# ---------------------------------------------------------------------------
# TranslationEntry
# ---------------------------------------------------------------------------
class TestTranslationEntry:
    """Tests for the TranslationEntry dataclass."""

    def test_basic_creation(self):
        entry = TranslationEntry(source="hello", translations={"ar": "مرحبا"})
        assert entry.source == "hello"
        assert entry.translations["ar"] == "مرحبا"

    def test_get_existing_lang(self):
        entry = TranslationEntry(source="hello", translations={"ar": "مرحبا", "fr": "bonjour"})
        assert entry.get("ar") == "مرحبا"
        assert entry.get("fr") == "bonjour"

    def test_get_missing_lang_default(self):
        entry = TranslationEntry(source="hello", translations={"ar": "مرحبا"})
        assert entry.get("zh") is None
        assert entry.get("zh", "fallback") == "fallback"

    def test_languages(self):
        entry = TranslationEntry(source="hello", translations={"ar": "مرحبا", "fr": "bonjour"})
        assert entry.languages() == {"ar", "fr"}

    def test_empty_translations(self):
        entry = TranslationEntry(source="hello")
        assert entry.languages() == set()
        assert entry.get("ar") is None

    def test_frozen(self):
        entry = TranslationEntry(source="hello", translations={"ar": "مرحبا"})
        with pytest.raises(AttributeError):
            entry.source = "other"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# TranslationMapping — creation
# ---------------------------------------------------------------------------
class TestTranslationMappingCreation:
    """Tests for TranslationMapping construction."""

    def test_default_empty(self):
        m = TranslationMapping()
        assert m.new == {}
        assert m.title == {}
        assert m.title_new == {}
        assert m.tspans_by_id == {}
        assert m.meta == {}

    def test_with_data(self):
        m = TranslationMapping(
            new={"hello": {"ar": "مرحبا"}},
            title={"t": {"ar": "ع"}},
            title_new={"t {year}": {"ar": "ع {year}"}},
            tspans_by_id={"t0": "hello"},
            meta={"source": "test"},
        )
        assert m.new["hello"]["ar"] == "مرحبا"
        assert m.meta["source"] == "test"


# ---------------------------------------------------------------------------
# Factory methods
# ---------------------------------------------------------------------------
class TestTranslationMappingFactory:
    """Tests for from_any and from_extractor_data."""

    def test_from_any_with_dict(self):
        data = {"new": {"hello": {"ar": "مرحبا"}}, "title": {}, "title_new": {}}
        m = TranslationMapping.from_any(data)
        assert "hello" in m.new

    def test_from_any_with_mapping(self):
        original = TranslationMapping(new={"x": {"ar": "y"}})
        result = TranslationMapping.from_any(original)
        assert result is original

    def test_from_any_minimal_dict(self):
        m = TranslationMapping.from_any({})
        assert m.new == {}

    def test_from_any_legacy_format(self):
        """Legacy format where 'new' key is absent and the dict itself is the map."""
        data = {"hello": {"ar": "مرحبا"}}
        m = TranslationMapping.from_any(data)
        # When 'new' is not a key, the whole dict becomes .new
        assert "hello" in m.new

    def test_from_extractor_data(self):
        data = {"new": {"hello": {"ar": "مرحبا"}}, "tspans_by_id": {"t0": "hello"}}
        m = TranslationMapping.from_extractor_data(data)
        assert "hello" in m.new
        assert m.tspans_by_id["t0"] == "hello"


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------
class TestTranslationMappingQuery:
    """Tests for query helpers."""

    def test_is_empty_true(self):
        m = TranslationMapping()
        assert m.is_empty() is True

    def test_is_empty_false_new(self):
        m = TranslationMapping(new={"x": {"ar": "y"}})
        assert m.is_empty() is False

    def test_is_empty_false_title(self):
        m = TranslationMapping(title={"x": {"ar": "y"}})
        assert m.is_empty() is False

    def test_is_empty_false_title_new(self):
        m = TranslationMapping(title_new={"x": {"ar": "y"}})
        assert m.is_empty() is False

    def test_all_languages(self):
        m = TranslationMapping(
            new={"a": {"ar": "1", "fr": "2"}},
            title={"b": {"de": "3"}},
            title_new={"c": {"es": "4"}},
        )
        assert m.all_languages() == {"ar", "fr", "de", "es"}

    def test_all_languages_empty(self):
        m = TranslationMapping()
        assert m.all_languages() == set()

    def test_lookup_case_insensitive(self):
        m = TranslationMapping(new={"Hello": {"ar": "مرحبا"}})
        result = m.lookup("hello", case_insensitive=True)
        assert result == {"ar": "مرحبا"}

    def test_lookup_case_sensitive(self):
        m = TranslationMapping(new={"Hello": {"ar": "مرحبا"}})
        result = m.lookup("Hello", case_insensitive=False)
        assert result == {"ar": "مرحبا"}
        result2 = m.lookup("hello", case_insensitive=False)
        assert result2 == {}

    def test_lookup_missing(self):
        m = TranslationMapping(new={"hello": {"ar": "مرحبا"}})
        result = m.lookup("world")
        assert result == {}

    def test_entries(self):
        m = TranslationMapping(new={"a": {"ar": "1"}, "b": {"fr": "2"}})
        entries = list(m.entries())
        assert len(entries) == 2
        assert all(isinstance(e, TranslationEntry) for e in entries)
        sources = {e.source for e in entries}
        assert sources == {"a", "b"}


# ---------------------------------------------------------------------------
# Mutation helpers
# ---------------------------------------------------------------------------
class TestTranslationMappingMutation:
    """Tests for add, merge, and to_json."""

    def test_add_case_insensitive(self):
        m = TranslationMapping()
        m.add("Hello", "ar", "مرحبا")
        assert "hello" in m.new
        assert m.new["hello"]["ar"] == "مرحبا"

    def test_add_case_sensitive(self):
        m = TranslationMapping()
        m.add("Hello", "ar", "مرحبا", case_insensitive=False)
        assert "Hello" in m.new

    def test_add_multiple_languages(self):
        m = TranslationMapping()
        m.add("hello", "ar", "مرحبا")
        m.add("hello", "fr", "bonjour")
        assert m.new["hello"] == {"ar": "مرحبا", "fr": "bonjour"}

    def test_merge_mappings(self):
        m1 = TranslationMapping(new={"a": {"ar": "1"}})
        m2 = TranslationMapping(new={"b": {"fr": "2"}}, title={"t": {"ar": "3"}})
        m1.merge(m2)
        assert "a" in m1.new
        assert "b" in m1.new
        assert "t" in m1.title

    def test_merge_overlapping(self):
        m1 = TranslationMapping(new={"a": {"ar": "1"}})
        m2 = TranslationMapping(new={"a": {"fr": "2"}})
        m1.merge(m2)
        assert m1.new["a"] == {"ar": "1", "fr": "2"}

    def test_merge_dict(self):
        m = TranslationMapping()
        m.merge({"new": {"x": {"ar": "y"}}, "title": {}, "title_new": {}})
        assert "x" in m.new

    def test_merge_updates_tspans_by_id(self):
        m1 = TranslationMapping(tspans_by_id={"t0": "hello"})
        m2 = TranslationMapping(tspans_by_id={"t1": "world"})
        m1.merge(m2)
        assert m1.tspans_by_id == {"t0": "hello", "t1": "world"}

    def test_to_json(self):
        m = TranslationMapping(
            new={"a": {"ar": "1"}},
            title={"t": {"ar": "2"}},
            title_new={"t {year}": {"ar": "2 {year}"}},
            tspans_by_id={"t0": "a"},
            meta={"source": "test"},
        )
        data = m.to_json()
        assert data["new"] == {"a": {"ar": "1"}}
        assert data["title"] == {"t": {"ar": "2"}}
        assert data["title_new"] == {"t {year}": {"ar": "2 {year}"}}
        assert data["tspans_by_id"] == {"t0": "a"}
        # assert data["meta"] == {"source": "test"}

    def test_to_json_roundtrip(self):
        m = TranslationMapping(new={"x": {"ar": "y"}}, title={"t": {"ar": "z"}})
        data = m.to_json()
        m2 = TranslationMapping.from_any(data)
        assert m2.new == m.new
        assert m2.title == m.title
