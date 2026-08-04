"""
Unit tests for CopySVGTranslation/preparation/steps/reorder.py module.

Classes to test: ReorderTexts

TODO: write tests
"""

from pathlib import Path
from types import SimpleNamespace

import pytest
from lxml import etree

from CopySVGTranslation.config import TranslationConfig
from CopySVGTranslation.preparation.preparer import PreparationContext
from CopySVGTranslation.preparation.steps.reorder import (
    ReorderTexts,
)

SVG_NS = "http://www.w3.org/2000/svg"

# ---------------------------------------------------------------------------
# ReorderTexts
# ---------------------------------------------------------------------------


def make_root(svg_body: str) -> etree._Element:
    """Build a standalone <svg> root element with the given inner XML."""
    xml = f'<svg xmlns="{SVG_NS}">{svg_body}</svg>'
    return etree.fromstring(xml)


def make_ctx(root: etree._Element | None = None, **overrides) -> PreparationContext:
    """Lightweight context stub carrying the attributes these steps read."""
    defaults = {
        "root": root,
        "tree": None,
        "translatable_nodes": [],
        "warnings": [],
        "config": TranslationConfig(assign_missing_ids=True),
        "path": Path("dummy.svg"),
    }
    defaults.update(overrides)
    return PreparationContext(**defaults)


@pytest.fixture
def reorder_step():

    return ReorderTexts(config=SimpleNamespace())


class TestReorderTexts:
    def test_root_none_is_a_noop(self, reorder_step):
        ctx = make_ctx(root=None)

        reorder_step.execute(ctx)

    def test_texts_sorted_by_numeric_id_within_switch(self, reorder_step):
        root = make_root(
            "<switch>"
            '<text id="trsvg3" systemLanguage="fr">c</text>'
            '<text id="trsvg1" systemLanguage="ar">a</text>'
            '<text id="trsvg2" systemLanguage="en">b</text>'
            "</switch>"
        )
        ctx = make_ctx(root=root)

        reorder_step.execute(ctx)

        switch = root.find(f".//{{{SVG_NS}}}switch")
        ids = [t.get("id") for t in switch]
        assert ids == ["trsvg1", "trsvg2", "trsvg3"]

    def test_fallback_text_is_placed_last(self, reorder_step):
        root = make_root(
            '<switch><text id="trsvg1">fallback</text><text id="trsvg2" systemLanguage="ar">a</text></switch>'
        )
        ctx = make_ctx(root=root)

        reorder_step.execute(ctx)

        switch = root.find(f".//{{{SVG_NS}}}switch")
        children = list(switch)
        assert children[-1].get("systemLanguage") is None

    def test_multiple_switches_are_each_sorted_independently(self, reorder_step):
        root = make_root(
            "<switch>"
            '<text id="trsvg2" systemLanguage="fr">b</text>'
            '<text id="trsvg1" systemLanguage="ar">a</text>'
            "</switch>"
            "<switch>"
            '<text id="trsvg9" systemLanguage="en">e</text>'
            '<text id="trsvg5" systemLanguage="de">d</text>'
            "</switch>"
        )
        ctx = make_ctx(root=root)

        reorder_step.execute(ctx)

        switches = root.findall(f".//{{{SVG_NS}}}switch")
        assert [t.get("id") for t in switches[0]] == ["trsvg1", "trsvg2"]
        assert [t.get("id") for t in switches[1]] == ["trsvg5", "trsvg9"]

    def test_no_switches_is_a_noop(self, reorder_step):
        root = make_root('<text id="t1">hello</text>')
        ctx = make_ctx(root=root)

        # should not raise even without any <switch> elements
        reorder_step.execute(ctx)
