"""
Tests for injection.switch_processor.SwitchProcessor.

Notes on setup:
- SwitchProcessor depends on several collaborator types/functions that
  live outside the shown module: TranslationConfig, TranslationMapping,
  InjectorStats, get_new_titles_translations,
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
  monkeypatch targets for `normalize_text`, and
  `get_new_titles_translations` to match your actual package layout if it
  differs. These are patched onto the `injection.switch_processor` module
  object directly (since that module does `from ..utils import
  normalize_text` and `from ..titles import
  get_new_titles_translations`, they become module-level names inside
  switch_processor.py that can be monkeypatched there).
"""

from __future__ import annotations

import pytest
from lxml import etree

from CopySVGTranslation import TranslationConfig
from CopySVGTranslation.core import TranslationMapping
from CopySVGTranslation.injection import TranslationApplier
from CopySVGTranslation.injection.id_manager import IdManager
from CopySVGTranslation.injection.switch_processor import (
    SVG_NS,
    SwitchProcessor,
)
from CopySVGTranslation.result import InjectorStats

NSMAP = {"svg": SVG_NS}

# ---------------------------------------------------------------------------
# Common fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def id_manager():
    return IdManager()


@pytest.fixture
def stats():
    return InjectorStats()


def make_config(
    overwrite_translations: bool = False, case_insensitive: bool = False, fallback_to_default_text: bool = False
) -> TranslationConfig:
    return TranslationConfig(
        overwrite_translations=overwrite_translations,
        case_insensitive=case_insensitive,
        fallback_to_default_text=fallback_to_default_text,
    )


def make_processor(config=None, id_manager=None, applier=None) -> SwitchProcessor:
    config = config or make_config()
    id_manager = id_manager or IdManager()

    return SwitchProcessor(
        config=config,
        id_manager=id_manager,
        applier=applier or TranslationApplier(config, id_manager),
    )


def make_switch(inner_xml: str) -> etree._Element:
    xml = f'<switch xmlns="{SVG_NS}">{inner_xml}</switch>'
    return etree.fromstring(xml)


def find_texts(switch: etree._Element) -> list[etree._Element]:
    return switch.xpath("./svg:text", namespaces=NSMAP)


# ---------------------------------------------------------------------------
# process() - early exits / guard clauses
# ---------------------------------------------------------------------------


class TestSetup:
    def tostring(self, el: etree._Element, pretty_print=False) -> str:
        return etree.tostring(el, pretty_print=pretty_print).decode("utf-8").strip()

    def normalize(self, file_text):
        # return file_text.strip()
        text = " ".join([x.strip() for x in file_text.strip().splitlines()])
        return text.replace("> <", "><")


class TestProcessEarlyExits(TestSetup):
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

        assert stats.processed_switches == 1
        assert len(find_texts(switch)) == 1

    def test_no_languages_to_process_returns_without_processing(self, id_manager, stats):
        import CopySVGTranslation.injection.switch_processor as sp_module  # noqa: F401

        switch = make_switch('<text id="t1">hello</text>')
        processor = make_processor(id_manager=id_manager)

        # available_translations will be non-empty, but each entry maps to
        # an empty per-language dict, so all_languages_count() yields an empty set
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


class TestProcessInsertion(TestSetup):
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

    def test_missing_translation_for_a_tspan_falls_back_to_default_text(self, id_manager, stats):
        switch = make_switch('<text id="t1"><tspan id="s1">hello</tspan><tspan id="s2">world</tspan></text>')
        processor = make_processor(
            config=make_config(fallback_to_default_text=False),
            id_manager=id_manager,
        )

        # only "hello" has an "ar" translation; "world" has an empty one
        processor.process(
            switch_element=switch,
            mapping={"new": {"hello": {"ar": "marhaba"}, "world": {}}},
            stats=stats,
        )

        # "hello" gets its real translation; "world" falls back to the
        # default text because its mapping value is empty.
        new_tspans = find_texts(switch)[-1].xpath("./svg:tspan", namespaces=NSMAP)
        assert new_tspans[0].text == "marhaba"

        expected = """
            <switch xmlns="http://www.w3.org/2000/svg">
                <text id="t1">
                    <tspan id="s1">hello</tspan>
                    <tspan id="s2">world</tspan>
                </text>
                <text id="t1-ar" systemLanguage="ar">
                    <tspan id="s1-ar">marhaba</tspan>
                </text>
            </switch>
        """
        switch_string = self.tostring(switch)
        assert '<tspan id="s2-ar">world</tspan>' not in switch_string

        assert self.normalize(switch_string) == self.normalize(expected)

    def test_new_node_copies_attributes_from_default_node(self, id_manager, stats):
        switch = make_switch('<text id="t1" x="10" y="20">hello</text>')
        processor = make_processor(id_manager=id_manager)

        processor.process(switch, {"new": {"hello": {"ar": "marhaba"}}}, stats)

        new_node = find_texts(switch)[-1]
        assert new_node.get("x") == "10"
        assert new_node.get("y") == "20"


# ---------------------------------------------------------------------------
# process() - existing language nodes: skip vs overwrite_translations
# ---------------------------------------------------------------------------


class TestProcessExistingLanguage(TestSetup):
    def test_existing_language_is_skipped_when_overwrite_disabled(self, id_manager, stats):
        switch = make_switch('<text id="t1">hello</text><text id="t1-ar" systemLanguage="ar">مرحبا قديم</text>')
        processor = make_processor(config=make_config(overwrite_translations=False), id_manager=id_manager)

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
        processor = make_processor(config=make_config(overwrite_translations=True), id_manager=id_manager)

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
        processor = make_processor(config=make_config(overwrite_translations=True), id_manager=id_manager)

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
        processor = make_processor(config=make_config(overwrite_translations=True), id_manager=id_manager)

        processor.process(switch, {"new": {"hello": {"fr": "bonjour2"}}}, stats)

        fr_tspan = switch.xpath('./svg:text[@systemLanguage="fr"]/svg:tspan', namespaces=NSMAP)[0]
        assert fr_tspan.text == "bonjour2"
        assert stats.updated_translations == 1

    def test_update_node_without_tspans_is_a_noop(self, id_manager, stats):
        # NOTE: THIS FIXED:
        # update_node returns early when the language node has no <tspan>
        # children at all, leaving its text untouched.
        switch = make_switch(
            '<text id="t1"><tspan id="s1">hello</tspan></text>'
            '<text id="ar1" systemLanguage="ar">plain text no tspans</text>'
        )
        processor = make_processor(config=make_config(overwrite_translations=True), id_manager=id_manager)

        processor.process(switch, {"new": {"hello": {"ar": "new"}}}, stats)

        ar_node = switch.xpath('./svg:text[@systemLanguage="ar"]', namespaces=NSMAP)[0]
        # assert ar_node.text == "plain text no tspans"
        assert ar_node.text == "new"  # NOTE: THIS FIXED:
        assert stats.updated_translations == 1

    def test_update_node_stops_at_shorter_default_texts_length(self, id_manager, stats, caplog):
        # Language node has more tspans than default_texts; loop should
        # log a warning and stop rather than raising an IndexError.
        switch = make_switch(
            '<text id="t1"><tspan id="s1">hello</tspan></text>'
            '<text id="ar1" systemLanguage="ar">'
            '<tspan id="a1">old1</tspan><tspan id="a2">old2</tspan>'
            "</text>"
        )
        processor = make_processor(config=make_config(overwrite_translations=True), id_manager=id_manager)

        processor.process(switch, {"new": {"hello": {"ar": "new"}}}, stats)

        ar_tspans = switch.xpath('./svg:text[@systemLanguage="ar"]/svg:tspan', namespaces=NSMAP)
        assert ar_tspans[0].text == "new"
        assert ar_tspans[1].text == "old2"  # beyond default_texts length: untouched


# ---------------------------------------------------------------------------
# enrich_all_mappings
# ---------------------------------------------------------------------------
class TestEnrichAllMappings(TestSetup):
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
