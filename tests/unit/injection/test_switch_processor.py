"""
Tests for injection.switch_processor.SwitchProcessor.

Notes on setup:
- SwitchProcessor depends on several collaborator types/functions that
  live outside the shown module: TranslationConfig, TranslationMapping,
  InjectorStats, get_new_titles_translations, _extract_text_from_node,
  normalize_text, and IdManager. Rather than importing the real package
  (not available alongside this file), we provide small, behavior-accurate
  fakes/stubs for each, matching exactly how SwitchProcessor calls them:

    * TranslationMapping.from_any(mapping) -> object with `.title_new` and
      `.new` (a dict of {original_text: {lang: translated_text}}).
      like {"new": {...}, "title_new": {...}}.

    * normalize_text(text, case_insensitive=False) -> str. Our fake trims
      whitespace and optionally lowercases, which is enough to exercise
      the case_insensitive branches without needing exact production
      semantics.

    * get_new_titles_translations(title_new, default_texts) -> dict shaped
      like mapping ({key: {lang: translated}}), merged into
      mapping.new via setdefault(...).update(...).

    * IdManager.allocate_clone(base_id, lang) -> str. Our fake returns a
      deterministic "{base_id}-{lang}" and records every call for
      assertions.

    * InjectorStats: a plain counter object with the four int attributes
      SwitchProcessor increments (skipped_translations,
      updated_translations, inserted_translations, processed_switches).

  Adjust the import path below (`injection.switch_processor`) and the
  monkeypatch targets for `_extract_text_from_node`, `normalize_text`, and
  `get_new_titles_translations` to match your actual package layout if it
  differs. These are patched onto the `injection.switch_processor` module
  object directly (since that module does `from ..utils import
  _extract_text_from_node, normalize_text` and `from ..titles import
  get_new_titles_translations`, they become module-level names inside
  switch_processor.py that can be monkeypatched there).
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from lxml import etree

from CopySVGTranslation import InjectorStats, TranslationConfig
from CopySVGTranslation.core import TranslationMapping
from CopySVGTranslation.injection.id_manager import IdManager
from CopySVGTranslation.injection.switch_processor import (
    SVG_NS,
    SwitchProcessor,
    _extract_text_from_node,
)

NSMAP = {"svg": SVG_NS}

# ---------------------------------------------------------------------------
# Fakes / stubs for SwitchProcessor's collaborators
# ---------------------------------------------------------------------------


def fake_extract_text_from_node(node: etree._Element) -> list[str]:
    """
    Return one text entry per <tspan> child (document order), or a single
    entry with the node's own direct text if there are no <tspan> children.
    This mirrors the positional pairing SwitchProcessor relies on between
    default_texts and each language node's <tspan> children.
    """
    tspans = node.xpath("./svg:tspan", namespaces=NSMAP)
    if tspans:
        return [t.text or "" for t in tspans]
    return [node.text or ""]


# ---------------------------------------------------------------------------
# Common fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def id_manager():
    return IdManager()


@pytest.fixture
def stats():
    return InjectorStats()


def make_config(overwrite: bool = False, case_insensitive: bool = False) -> TranslationConfig:
    return TranslationConfig(overwrite=overwrite, case_insensitive=case_insensitive)


def make_processor(config=None, id_manager=None, applier=None) -> SwitchProcessor:
    return SwitchProcessor(
        config=config or make_config(),
        id_manager=id_manager or IdManager(),
        applier=applier or SimpleNamespace(),
    )


def make_switch(inner_xml: str) -> etree._Element:
    xml = f'<switch xmlns="{SVG_NS}">{inner_xml}</switch>'
    return etree.fromstring(xml)


def find_texts(switch: etree._Element) -> list[etree._Element]:
    return switch.xpath("./svg:text", namespaces=NSMAP)


# ---------------------------------------------------------------------------
# process() - early exits / guard clauses
# ---------------------------------------------------------------------------


class TestProcessEarlyExits:
    def test_no_text_children_returns_without_processing(self, id_manager, stats):
        switch = make_switch('<g><text id="t1">hello</text></g>')  # text nested, not a direct child
        processor = make_processor(id_manager=id_manager)

        processor.process(switch, {"new": {}}, stats)

        assert stats.processed_switches == 0

    def test_no_fallback_default_node_returns_without_processing(self, id_manager, stats):
        # Every <text> has a systemLanguage, so no default/fallback node exists
        switch = make_switch('<text id="t1" systemLanguage="ar">hello</text>')
        processor = make_processor(id_manager=id_manager)

        processor.process(switch, {"new": {}}, stats)

        assert stats.processed_switches == 0

    def test_no_available_translations_returns_without_processing(self, id_manager, stats):
        switch = make_switch('<text id="t1">hello</text>')
        processor = make_processor(id_manager=id_manager)

        # mapping has no entry matching "hello"
        processor.process(switch, {"new": {"something else": {"ar": "شيء آخر"}}}, stats)

        assert stats.processed_switches == 0
        assert len(find_texts(switch)) == 1

    def test_no_languages_to_process_returns_without_processing(self, id_manager, stats):
        import CopySVGTranslation.injection.switch_processor as sp_module  # noqa: F401

        switch = make_switch('<text id="t1">hello</text>')
        processor = make_processor(id_manager=id_manager)

        # available_translations will be non-empty, but each entry maps to
        # an empty per-language dict, so all_languages() yields an empty set
        processor.process(switch, {"new": {"hello": {}}}, stats)

        assert stats.processed_switches == 0

    def test_accepts_plain_dict_mapping_via_from_any(self, id_manager, stats):
        # mapping passed as a raw dict (not a TranslationMapping instance)
        switch = make_switch('<text id="t1">hello</text>')
        processor = make_processor(id_manager=id_manager)

        processor.process(switch, {"new": {"hello": {"ar": "مرحبا"}}}, stats)

        assert stats.processed_switches == 1
        assert stats.inserted_translations == 1

    def test_accepts_translation_mapping_instance_directly(self, id_manager, stats):
        switch = make_switch('<text id="t1">hello</text>')
        processor = make_processor(id_manager=id_manager)
        mapping = TranslationMapping(new={"hello": {"ar": "مرحبا"}})

        processor.process(switch, mapping, stats)

        assert stats.processed_switches == 1


# ---------------------------------------------------------------------------
# process() - insertion of new language nodes
# ---------------------------------------------------------------------------


class TestProcessInsertion:
    def test_inserts_new_node_for_missing_language(self, id_manager, stats):
        switch = make_switch('<text id="t1">hello</text>')
        processor = make_processor(id_manager=id_manager)

        processor.process(switch, {"new": {"hello": {"ar": "مرحبا"}}}, stats)

        texts = find_texts(switch)
        assert len(texts) == 2
        new_node = texts[-1]
        assert new_node.get("systemLanguage") == "ar"
        assert new_node.text == "مرحبا"
        assert stats.inserted_translations == 1
        assert stats.processed_switches == 1

    def test_new_node_id_is_allocated_via_id_manager(self, id_manager, stats):
        switch = make_switch('<text id="t1">hello</text>')
        processor = make_processor(id_manager=id_manager)

        processor.process(switch, {"new": {"hello": {"ar": "مرحبا"}}}, stats)

        assert id_manager.existing_ids == {"t1-ar"}
        new_node = find_texts(switch)[-1]
        assert new_node.get("id") == "t1-ar"

    def test_new_node_without_original_id_has_no_id(self, id_manager, stats):
        switch = make_switch("<text>hello</text>")
        processor = make_processor(id_manager=id_manager)

        processor.process(switch, {"new": {"hello": {"ar": "مرحبا"}}}, stats)

        new_node = find_texts(switch)[-1]
        assert new_node.get("id") is None
        assert id_manager.existing_ids == set()

    def test_multiple_target_languages_each_create_a_node(self, id_manager, stats):
        switch = make_switch('<text id="t1">hello</text>')
        processor = make_processor(id_manager=id_manager)

        processor.process(
            switch,
            {"new": {"hello": {"ar": "مرحبا", "fr": "bonjour"}}},
            stats,
        )

        texts = find_texts(switch)
        assert len(texts) == 3
        langs = {t.get("systemLanguage") for t in texts[1:]}
        assert langs == {"ar", "fr"}
        assert stats.inserted_translations == 2

    def test_tspans_are_translated_individually_in_new_node(self, id_manager, stats):
        switch = make_switch('<text id="t1"><tspan id="s1">hello</tspan><tspan id="s2">world</tspan></text>')
        processor = make_processor(id_manager=id_manager)

        processor.process(
            switch,
            {
                "new": {
                    "hello": {"ar": "مرحبا"},
                    "world": {"ar": "عالم"},
                }
            },
            stats,
        )

        new_node = find_texts(switch)[-1]
        new_tspans = new_node.xpath("./svg:tspan", namespaces=NSMAP)
        assert len(new_tspans) == 2
        assert new_tspans[0].text == "مرحبا"
        assert new_tspans[1].text == "عالم"

    def test_tspan_ids_are_cloned_independently(self, id_manager, stats):
        switch = make_switch('<text id="t1"><tspan id="s1">hello</tspan></text>')
        processor = make_processor(id_manager=id_manager)

        processor.process(switch, {"new": {"hello": {"ar": "مرحبا"}}}, stats)

        assert id_manager.existing_ids == {"s1-ar", "t1-ar"}

        new_tspan = find_texts(switch)[-1].xpath("./svg:tspan", namespaces=NSMAP)[0]
        assert new_tspan.get("id") == "s1-ar"

    def test_missing_translation_for_a_tspan_falls_back_to_empty_string(self, id_manager, stats):
        switch = make_switch('<text id="t1"><tspan id="s1">hello</tspan><tspan id="s2">world</tspan></text>')
        processor = make_processor(id_manager=id_manager)

        # only "hello" has an "ar" translation; "world" has none
        processor.process(switch, {"new": {"hello": {"ar": "مرحبا"}, "world": {}}}, stats)

        # "world" alone would not surface "ar" as a language to process,
        # but since "hello" does, "ar" is still processed and the
        # untranslated tspan falls back to "".
        new_tspans = find_texts(switch)[-1].xpath("./svg:tspan", namespaces=NSMAP)
        assert new_tspans[0].text == "مرحبا"
        assert new_tspans[1].text == ""

    def test_new_node_copies_attributes_from_default_node(self, id_manager, stats):
        switch = make_switch('<text id="t1" x="10" y="20">hello</text>')
        processor = make_processor(id_manager=id_manager)

        processor.process(switch, {"new": {"hello": {"ar": "مرحبا"}}}, stats)

        new_node = find_texts(switch)[-1]
        assert new_node.get("x") == "10"
        assert new_node.get("y") == "20"


# ---------------------------------------------------------------------------
# process() - existing language nodes: skip vs overwrite
# ---------------------------------------------------------------------------


class TestProcessExistingLanguage:
    def test_existing_language_is_skipped_when_overwrite_disabled(self, id_manager, stats):
        switch = make_switch('<text id="t1">hello</text><text id="t1-ar" systemLanguage="ar">مرحبا قديم</text>')
        processor = make_processor(config=make_config(overwrite=False), id_manager=id_manager)

        processor.process(switch, {"new": {"hello": {"ar": "مرحبا جديد"}}}, stats)

        ar_node = switch.xpath('./svg:text[@systemLanguage="ar"]', namespaces=NSMAP)[0]
        assert stats.skipped_translations == 1
        assert stats.updated_translations == 0
        assert stats.inserted_translations == 0
        # text content is untouched since update_node is never called
        assert ar_node.text == "مرحبا قديم"

    def test_existing_language_is_updated_when_overwrite_enabled(self, id_manager, stats):
        switch = make_switch(
            '<text id="t1"><tspan id="s1">hello</tspan></text>'
            '<text id="t1-ar" systemLanguage="ar"><tspan id="s1-ar">مرحبا قديم</tspan></text>'
        )
        processor = make_processor(config=make_config(overwrite=True), id_manager=id_manager)

        processor.process(switch, {"new": {"hello": {"ar": "مرحبا جديد"}}}, stats)

        ar_tspan = switch.xpath('./svg:text[@systemLanguage="ar"]/svg:tspan', namespaces=NSMAP)[0]

        assert ar_tspan.text == "مرحبا جديد"
        assert stats.updated_translations == 1
        assert stats.skipped_translations == 0
        assert stats.inserted_translations == 0

    def test_only_first_matching_language_node_is_updated(self, id_manager, stats):
        # Two "ar" nodes exist (unusual, but exercises the `break` after
        # the first update_node call inside the update loop).
        switch = make_switch(
            '<text id="t1"><tspan id="s1">hello</tspan></text>'
            '<text id="a1" systemLanguage="ar"><tspan id="a1s">old1</tspan></text>'
            '<text id="a2" systemLanguage="ar"><tspan id="a2s">old2</tspan></text>'
        )
        processor = make_processor(config=make_config(overwrite=True), id_manager=id_manager)

        processor.process(switch, {"new": {"hello": {"ar": "new"}}}, stats)

        ar_nodes = switch.xpath('./svg:text[@systemLanguage="ar"]', namespaces=NSMAP)
        first_tspan = ar_nodes[0].xpath("./svg:tspan", namespaces=NSMAP)[0]
        second_tspan = ar_nodes[1].xpath("./svg:tspan", namespaces=NSMAP)[0]
        assert first_tspan.text == "new"
        assert second_tspan.text == "old2"  # untouched: loop breaks after first match
        assert stats.updated_translations == 1

    def test_update_node_ignores_node_with_different_language(self, id_manager, stats):
        # update_node's own guard: node.get("systemLanguage") != lang -> no-op.
        # Exercised indirectly: the FR node is present but the target lang is AR,
        # so if update_node were mistakenly called on the FR node, nothing changes.
        switch = make_switch(
            '<text id="t1"><tspan id="s1">hello</tspan></text>'
            '<text id="fr1" systemLanguage="fr"><tspan id="frs">bonjour</tspan></text>'
        )
        processor = make_processor(config=make_config(overwrite=True), id_manager=id_manager)

        processor.process(switch, {"new": {"hello": {"fr": "bonjour2"}}}, stats)

        fr_tspan = switch.xpath('./svg:text[@systemLanguage="fr"]/svg:tspan', namespaces=NSMAP)[0]
        assert fr_tspan.text == "bonjour2"
        assert stats.updated_translations == 1

    def test_update_node_without_tspans_is_a_noop(self, id_manager, stats):
        # update_node returns early when the language node has no <tspan>
        # children at all, leaving its text untouched.
        switch = make_switch(
            '<text id="t1"><tspan id="s1">hello</tspan></text>'
            '<text id="ar1" systemLanguage="ar">plain text no tspans</text>'
        )
        processor = make_processor(config=make_config(overwrite=True), id_manager=id_manager)

        processor.process(switch, {"new": {"hello": {"ar": "new"}}}, stats)

        ar_node = switch.xpath('./svg:text[@systemLanguage="ar"]', namespaces=NSMAP)[0]
        assert ar_node.text == "plain text no tspans"
        assert stats.updated_translations == 1  # still counted, even though nothing changed

    def test_update_node_stops_at_shorter_default_texts_length(self, id_manager, stats, caplog):
        # Language node has more tspans than default_texts; loop should
        # log a warning and stop rather than raising an IndexError.
        switch = make_switch(
            '<text id="t1"><tspan id="s1">hello</tspan></text>'
            '<text id="ar1" systemLanguage="ar">'
            '<tspan id="a1">old1</tspan><tspan id="a2">old2</tspan>'
            "</text>"
        )
        processor = make_processor(config=make_config(overwrite=True), id_manager=id_manager)

        processor.process(switch, {"new": {"hello": {"ar": "new"}}}, stats)

        ar_tspans = switch.xpath('./svg:text[@systemLanguage="ar"]/svg:tspan', namespaces=NSMAP)
        assert ar_tspans[0].text == "new"
        assert ar_tspans[1].text == "old2"  # beyond default_texts length: untouched


# ---------------------------------------------------------------------------
# get_default_texts
# ---------------------------------------------------------------------------


class TestGetDefaultTexts:
    def test_returns_first_node_without_systemlanguage(self, id_manager):
        processor = make_processor(id_manager=id_manager)
        switch = make_switch('<text id="ar1" systemLanguage="ar">a</text><text id="t1">hello</text>')
        text_elements = find_texts(switch)

        default_node = processor.get_default_node(text_elements)
        default_texts = processor.get_default_texts(default_node)
        assert default_node is not None

        assert default_node.get("id") == "t1"
        assert default_texts == ["hello"]

    def test_returns_none_none_when_all_nodes_have_systemlanguage(self, id_manager):
        processor = make_processor(id_manager=id_manager)
        switch = make_switch('<text id="ar1" systemLanguage="ar">a</text>')
        text_elements = find_texts(switch)

        default_node = processor.get_default_node(text_elements)
        default_texts = processor.get_default_texts(default_node)

        assert default_texts == []
        assert default_node is None

    def test_texts_are_normalized_with_case_insensitive_flag(self, id_manager):
        processor = make_processor(config=make_config(case_insensitive=True), id_manager=id_manager)
        switch = make_switch('<text id="t1">  Hello  </text>')
        text_elements = find_texts(switch)

        default_node = processor.get_default_node(text_elements)
        default_texts = processor.get_default_texts(default_node)

        assert default_texts == ["hello"]


# ---------------------------------------------------------------------------
# get_existing_languages
# ---------------------------------------------------------------------------


class TestGetExistingLanguages:
    def test_collects_all_systemlanguage_values(self, id_manager):
        processor = make_processor(id_manager=id_manager)
        switch = make_switch(
            '<text id="t1">a</text>'
            '<text id="t2" systemLanguage="ar">b</text>'
            '<text id="t3" systemLanguage="fr">c</text>'
        )
        text_elements = find_texts(switch)

        existing = processor.get_existing_languages(text_elements)

        assert existing == {"ar", "fr"}

    def test_no_language_nodes_returns_empty_set(self, id_manager):
        processor = make_processor(id_manager=id_manager)
        switch = make_switch('<text id="t1">a</text>')
        text_elements = find_texts(switch)

        assert processor.get_existing_languages(text_elements) == set()


# ---------------------------------------------------------------------------
# enrich_all_mappings
# ---------------------------------------------------------------------------
class TestEnrichAllMappings:
    def test_merges_title_translations_into_new_mapping(self, id_manager):
        processor = make_processor(id_manager=id_manager)
        mapping = TranslationMapping(
            new={"hello 2020": {"ar": "مرحبا 2020"}},
            title_new={"hello {year}": {"de": "hallo {year}"}},
        )

        result = processor.enrich_all_mappings(mapping, ["hello 2020"])

        assert result.new["hello 2020"] == {"ar": "مرحبا 2020", "de": "hallo 2020"}

    def test_title_translations_can_introduce_new_keys(self, id_manager):
        processor = make_processor(id_manager=id_manager)
        mapping = TranslationMapping(
            new={"hello 2020": {"ar": "مرحبا 2020"}},
            title_new={"brand new key {year}": {"ar": "جديد {year}"}},
        )

        result = processor.enrich_all_mappings(mapping, ["brand new key 2020"])

        assert result.new["brand new key 2020"] == {"ar": "جديد 2020"}
        # original mapping.new must be unaffected (a copy is used)
        assert "brand new key 2020" not in mapping.new

    def test_does_not_overwrite_existing_language_for_existing_key(self, id_manager):
        # setdefault(key, {}).update(translations) means title-derived
        # languages are added/overwritten on top of the existing per-key
        # dict, not replacing the whole dict.
        processor = make_processor(id_manager=id_manager)
        mapping = TranslationMapping(
            new={"hello 2020": {"ar": "مرحبا 2020"}},
            title_new={"hello {year}": {"fr": "bonjour {year}"}},
        )

        result = processor.enrich_all_mappings(mapping, ["hello 2020"])

        assert result.new["hello 2020"] == {"ar": "مرحبا 2020", "fr": "bonjour 2020"}


# ---------------------------------------------------------------------------
# get_available_translations
# ---------------------------------------------------------------------------


class TestGetAvailableTranslations:
    def test_returns_only_texts_present_in_mappings(self, id_manager):
        processor = make_processor(id_manager=id_manager)

        result = processor.get_available_translations(["hello", "missing"], {"hello": {"ar": "مرحبا"}})

        assert result == {"hello": {"ar": "مرحبا"}}

    def test_case_insensitive_lookup_uses_lowercased_key(self, id_manager):
        processor = make_processor(config=make_config(case_insensitive=True), id_manager=id_manager)

        result = processor.get_available_translations(["Hello"], {"hello": {"ar": "مرحبا"}})

        assert result == {"hello": {"ar": "مرحبا"}}

    def test_empty_default_texts_returns_empty_dict(self, id_manager):
        processor = make_processor(id_manager=id_manager)

        assert processor.get_available_translations([], {"hello": {"ar": "مرحبا"}}) == {}


# ---------------------------------------------------------------------------
# all_languages
# ---------------------------------------------------------------------------


class TestAllLanguages:
    def test_collects_union_of_all_language_keys(self, id_manager):
        processor = make_processor(id_manager=id_manager)

        result = processor.all_languages(
            {"hello": {"ar": "مرحبا", "fr": "bonjour"}, "world": {"fr": "monde", "de": "welt"}}
        )

        assert result == {"ar", "fr", "de"}

    def test_empty_translations_returns_empty_set(self, id_manager):
        processor = make_processor(id_manager=id_manager)

        assert processor.all_languages({}) == set()


# ---------------------------------------------------------------------------
# get_key_lang (static method)
# ---------------------------------------------------------------------------


class TestGetKeyLang:
    def test_returns_translation_when_key_and_lang_present(self):
        result = make_processor().get_key_lang("hello", "ar", {"hello": {"ar": "مرحبا"}})
        assert result == "مرحبا"

    def test_returns_none_when_key_missing(self):
        result = make_processor().get_key_lang("missing", "ar", {"hello": {"ar": "مرحبا"}})
        assert result is None

    def test_returns_none_when_lang_missing_for_key(self):
        result = make_processor().get_key_lang("hello", "fr", {"hello": {"ar": "مرحبا"}})
        assert result is None

    def test_returns_none_when_key_is_none(self):
        result = make_processor().get_key_lang(None, "ar", {"hello": {"ar": "مرحبا"}})
        assert result is None

    def test_normalize_flag_applies_normalize_text_before_lookup(self):

        result = make_processor().get_key_lang("  hello  ", "ar", {"hello": {"ar": "مرحبا"}}, normalize=True)
        assert result == "مرحبا"

    def test_case_insensitive_fallback_when_exact_key_misses(self):
        processor = make_processor(config=make_config(case_insensitive=True))
        result = processor.get_key_lang("Hello", "ar", {"hello": {"ar": "مرحبا"}})
        assert result == "مرحبا"

    def test_no_case_insensitive_fallback_when_flag_is_false(self):
        processor = make_processor(config=make_config(case_insensitive=False))
        result = processor.get_key_lang("Hello", "ar", {"hello": {"ar": "مرحبا"}})
        assert result is None

    def test_exact_match_is_tried_before_case_insensitive_fallback(self):
        # Both "Hello" (exact) and "hello" (lowercase) exist with different
        # translations; the exact match must win.
        data = {"Hello": {"ar": "مرحبا-exact"}, "hello": {"ar": "مرحبا-lower"}}
        processor = make_processor(config=make_config(case_insensitive=True))
        result = processor.get_key_lang("Hello", "ar", data)
        assert result == "مرحبا-exact"


class TestTextUtils:
    """Test cases for text utility functions."""

    def test_extract_text_from_node_with_tspans(self):
        """Test extracting text from a node with tspans."""
        svg_ns = "http://www.w3.org/2000/svg"
        text_node = etree.fromstring(f"""<text xmlns="{svg_ns}"><tspan>Hello</tspan><tspan>World</tspan></text>""")
        result = _extract_text_from_node(text_node)
        assert result == ["Hello", "World"]

    def test_extract_text_from_node_without_tspans(self):
        """Test extracting text from a node without tspans."""
        svg_ns = "http://www.w3.org/2000/svg"
        text_node = etree.fromstring(f'<text xmlns="{svg_ns}">Plain text</text>')
        result = _extract_text_from_node(text_node)
        assert result == ["Plain text"]

    def test_extract_text_from_node_empty(self):
        """Test extracting text from an empty node."""
        svg_ns = "http://www.w3.org/2000/svg"
        text_node = etree.fromstring(f'<text xmlns="{svg_ns}"></text>')
        result = _extract_text_from_node(text_node)
        assert result == [""]

    def test_extract_text_from_node_with_whitespace_tspans(self):
        """Test extracting text from tspans with only whitespace."""
        svg_ns = "http://www.w3.org/2000/svg"
        text_node = etree.fromstring(f"""<text xmlns="{svg_ns}"><tspan>   </tspan><tspan>Text</tspan></text>""")
        result = _extract_text_from_node(text_node)
        assert result == ["", "Text"]


class TestExtractTextFromNode:
    """Test suite for _extract_text_from_node function."""

    def test_extract_from_text_with_tspans(self):
        """Test extraction from text element with tspan children."""
        xml = """<text xmlns="http://www.w3.org/2000/svg">
            <tspan>First</tspan>
            <tspan>Second</tspan>
        </text>"""
        node = etree.fromstring(xml)
        result = _extract_text_from_node(node)

        assert result == ["First", "Second"]

    def test_extract_from_text_without_tspans(self):
        """Test extraction from text element without tspans."""
        xml = '<text xmlns="http://www.w3.org/2000/svg">Direct text</text>'
        node = etree.fromstring(xml)
        result = _extract_text_from_node(node)

        assert result == ["Direct text"]

    def test_extract_from_text_with_empty_tspans(self):
        """Test extraction with empty tspan elements."""
        xml = """<text xmlns="http://www.w3.org/2000/svg">
            <tspan></tspan>
            <tspan>Content</tspan>
        </text>"""
        node = etree.fromstring(xml)
        result = _extract_text_from_node(node)

        assert result == ["", "Content"]

    def test_extract_from_text_with_whitespace_tspans(self):
        """Test extraction handles whitespace in tspans."""
        xml = """<text xmlns="http://www.w3.org/2000/svg">
            <tspan>  Spaces  </tspan>
            <tspan>	Tabs	</tspan>
        </text>"""
        node = etree.fromstring(xml)
        result = _extract_text_from_node(node)

        assert result == ["Spaces", "Tabs"]

    def test_extract_from_empty_text_node(self):
        """Test extraction from empty text node."""
        xml = '<text xmlns="http://www.w3.org/2000/svg"></text>'
        node = etree.fromstring(xml)
        result = _extract_text_from_node(node)

        assert result == [""]

    def test_extract_with_unicode_content(self):
        """Test extraction with Unicode content."""
        xml = """<text xmlns="http://www.w3.org/2000/svg">
            <tspan>مرحبا</tspan>
            <tspan>你好</tspan>
            <tspan>Привет</tspan>
        </text>"""
        node = etree.fromstring(xml)
        result = _extract_text_from_node(node)

        assert result == ["مرحبا", "你好", "Привет"]

    def test_extract_text_from_node_with_multiple_tspans(self):
        """Test extracting text from node with multiple tspans."""
        svg_ns = "http://www.w3.org/2000/svg"
        text_node = etree.fromstring(f'<text xmlns="{svg_ns}"><tspan>Hello</tspan><tspan>World</tspan></text>')
        result = _extract_text_from_node(text_node)
        assert result == ["Hello", "World"]

    def test_extract_text_from_node_plain_text(self):
        """Test extracting plain text from node without tspans."""
        svg_ns = "http://www.w3.org/2000/svg"
        text_node = etree.fromstring(f'<text xmlns="{svg_ns}">Plain text</text>')
        result = _extract_text_from_node(text_node)
        assert result == ["Plain text"]
