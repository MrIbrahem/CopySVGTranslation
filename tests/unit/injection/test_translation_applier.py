"""
Unit tests for CopySVGTranslation/injection/translation_applier.py module.

Classes to test: ApplyResult, TranslationApplier
"""

from __future__ import annotations

from lxml import etree

from CopySVGTranslation.config import TranslationConfig
from CopySVGTranslation.injection.id_manager import IdManager
from CopySVGTranslation.injection.translation_applier import (
    ApplyResult,
    TranslationApplier,
)

SVG_NS = "http://www.w3.org/2000/svg"


def _make_text(text: str, id_: str = "t0", tspans: bool = True) -> etree._Element:
    """Create a simple SVG <text> element."""
    elem = etree.Element(f"{{{SVG_NS}}}text")
    elem.set("id", id_)
    if tspans:
        ts = etree.SubElement(elem, f"{{{SVG_NS}}}tspan")
        ts.set("id", f"{id_}-ts")
        ts.text = text
    else:
        elem.text = text
    return elem


def _make_applier(
    overwrite: bool = False,
    existing_ids: set[str] | None = None,
) -> TranslationApplier:
    config = TranslationConfig(overwrite=overwrite)
    id_mgr = IdManager(existing_ids)
    return TranslationApplier(config, id_mgr)


# ---------------------------------------------------------------------------
# ApplyResult dataclass
# ---------------------------------------------------------------------------
class TestApplyResult:
    """Tests for the ApplyResult dataclass."""

    def test_inserted_action(self):
        r = ApplyResult(action="inserted")
        assert r.action == "inserted"
        assert r.node is None

    def test_updated_action_with_node(self):
        node = etree.Element("text")
        r = ApplyResult(action="updated", node=node)
        assert r.action == "updated"
        assert r.node is node

    def test_skipped_action(self):
        r = ApplyResult(action="skipped")
        assert r.action == "skipped"


# ---------------------------------------------------------------------------
# TranslationApplier — insert (no existing node)
# ---------------------------------------------------------------------------
class TestApplyLanguageInsert:
    """Tests for inserting a new language node."""

    def test_insert_new_node_with_tspans(self):
        applier = _make_applier()
        default_node = _make_text("Hello", id_="t0")
        translations = {"Hello": "مرحبا"}
        result = applier.apply_language(
            default_node=default_node,
            default_texts=["Hello"],
            lang="ar",
            translations=translations,
            existing_lang_node=None,
        )
        assert result.action == "inserted"
        assert result.node is not None
        assert result.node.get("systemLanguage") == "ar"
        tspans = result.node.xpath("./svg:tspan", namespaces={"svg": SVG_NS})
        assert tspans[0].text == "مرحبا"

    def test_insert_new_node_without_tspans(self):
        applier = _make_applier()
        default_node = _make_text("Hello", id_="t0", tspans=False)
        translations = {"Hello": "Bonjour"}
        result = applier.apply_language(
            default_node=default_node,
            default_texts=["Hello"],
            lang="fr",
            translations=translations,
            existing_lang_node=None,
        )
        assert result.action == "inserted"
        assert result.node is not None
        assert result.node.text == "Bonjour"

    def test_insert_assigns_new_ids(self):
        applier = _make_applier(existing_ids={"t0", "t0-ts"})
        default_node = _make_text("Hello", id_="t0")
        translations = {"Hello": "مرحبا"}
        result = applier.apply_language(
            default_node=default_node,
            default_texts=["Hello"],
            lang="ar",
            translations=translations,
            existing_lang_node=None,
        )
        # The cloned node should have a new ID (not "t0")
        assert result.node.get("id") != "t0"

    def test_insert_missing_translation_fills_nothing(self):
        applier = _make_applier()
        default_node = _make_text("Hello", id_="t0")
        translations: dict[str, str] = {}  # no match for "Hello"
        result = applier.apply_language(
            default_node=default_node,
            default_texts=["Hello"],
            lang="fr",
            translations=translations,
            existing_lang_node=None,
        )
        assert result.action == "inserted"
        # tspan text should remain the original (cloned) text
        tspans = result.node.xpath("./svg:tspan", namespaces={"svg": SVG_NS})
        assert tspans[0].text == "Hello"

    def test_insert_empty_default_texts(self):
        applier = _make_applier()
        default_node = _make_text("", id_="t0", tspans=False)
        translations: dict[str, str] = {}
        result = applier.apply_language(
            default_node=default_node,
            default_texts=[],
            lang="fr",
            translations=translations,
            existing_lang_node=None,
        )
        assert result.action == "inserted"


# ---------------------------------------------------------------------------
# TranslationApplier — skip (existing node, overwrite=False)
# ---------------------------------------------------------------------------
class TestApplyLanguageSkip:
    """Tests for skipping an existing language node."""

    def test_skip_when_overwrite_false(self):
        applier = _make_applier(overwrite=False)
        default_node = _make_text("Hello", id_="t0")
        existing = _make_text("Hola", id_="t0-es")
        existing.set("systemLanguage", "es")
        result = applier.apply_language(
            default_node=default_node,
            default_texts=["Hello"],
            lang="es",
            translations={"Hello": "Hola nueva"},
            existing_lang_node=existing,
        )
        assert result.action == "skipped"
        assert result.node is existing

    def test_skip_preserves_existing_text(self):
        applier = _make_applier(overwrite=False)
        default_node = _make_text("Hello", id_="t0")
        existing = _make_text("Hola", id_="t0-es")
        existing.set("systemLanguage", "es")
        result = applier.apply_language(
            default_node=default_node,
            default_texts=["Hello"],
            lang="es",
            translations={"Hello": "Nueva"},
            existing_lang_node=existing,
        )
        tspans = result.node.xpath("./svg:tspan", namespaces={"svg": SVG_NS})
        assert tspans[0].text == "Hola"  # unchanged


# ---------------------------------------------------------------------------
# TranslationApplier — update (existing node, overwrite=True)
# ---------------------------------------------------------------------------
class TestApplyLanguageUpdate:
    """Tests for updating an existing language node."""

    def test_update_with_tspans(self):
        applier = _make_applier(overwrite=True)
        default_node = _make_text("Hello", id_="t0")
        existing = _make_text("Hola", id_="t0-es")
        existing.set("systemLanguage", "es")
        result = applier.apply_language(
            default_node=default_node,
            default_texts=["Hello"],
            lang="es",
            translations={"Hello": "Hola nueva"},
            existing_lang_node=existing,
        )
        assert result.action == "updated"
        tspans = result.node.xpath("./svg:tspan", namespaces={"svg": SVG_NS})
        assert tspans[0].text == "Hola nueva"

    def test_update_without_tspans(self):
        applier = _make_applier(overwrite=True)
        default_node = _make_text("Hello", id_="t0", tspans=False)
        existing = etree.Element(f"{{{SVG_NS}}}text")
        existing.set("systemLanguage", "fr")
        existing.text = "Bonjour old"
        result = applier.apply_language(
            default_node=default_node,
            default_texts=["Hello"],
            lang="fr",
            translations={"Hello": "Bonjour new"},
            existing_lang_node=existing,
        )
        assert result.action == "updated"
        assert result.node.text == "Bonjour new"

    def test_update_no_matching_translation(self):
        applier = _make_applier(overwrite=True)
        default_node = _make_text("Hello", id_="t0")
        existing = _make_text("Hola", id_="t0-es")
        existing.set("systemLanguage", "es")
        result = applier.apply_language(
            default_node=default_node,
            default_texts=["Hello"],
            lang="es",
            translations={},  # no match
            existing_lang_node=existing,
        )
        assert result.action == "updated"
        # Text should remain unchanged
        tspans = result.node.xpath("./svg:tspan", namespaces={"svg": SVG_NS})
        assert tspans[0].text == "Hola"

    def test_update_empty_default_texts(self):
        applier = _make_applier(overwrite=True)
        default_node = _make_text("", id_="t0", tspans=False)
        existing = etree.Element(f"{{{SVG_NS}}}text")
        existing.set("systemLanguage", "fr")
        existing.text = "old"
        result = applier.apply_language(
            default_node=default_node,
            default_texts=[],
            lang="fr",
            translations={},
            existing_lang_node=existing,
        )
        assert result.action == "updated"


# ---------------------------------------------------------------------------
# _reassign_ids
# ---------------------------------------------------------------------------
class TestReassignIds:
    """Tests for the _reassign_ids internal method."""

    def test_reassigns_element_id(self):
        applier = _make_applier(existing_ids={"orig"})
        elem = etree.Element(f"{{{SVG_NS}}}text")
        elem.set("id", "orig")
        applier._reassign_ids(elem, "ar")
        assert elem.get("id") != "orig"
        assert "ar" in elem.get("id", "")

    def test_reassigns_children_recursively(self):
        applier = _make_applier(existing_ids={"p", "c"})
        parent = etree.Element(f"{{{SVG_NS}}}text")
        parent.set("id", "p")
        child = etree.SubElement(parent, f"{{{SVG_NS}}}tspan")
        child.set("id", "c")
        applier._reassign_ids(parent, "fr")
        assert parent.get("id") != "p"
        assert child.get("id") != "c"

    def test_no_id_attribute(self):
        applier = _make_applier()
        elem = etree.Element(f"{{{SVG_NS}}}text")
        # No id set — should not crash; _reassign_ids only reassigns existing ids
        applier._reassign_ids(elem, "ar")
        # Element without id stays without id (only existing ids are reassigned)
        assert elem.get("id") is None
