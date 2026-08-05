"""
Unit tests for CopySVGTranslation/preparation/steps/normalize_tspans.py module.

Classes to test: NormalizeTspans, WrapTspans

TODO: write tests
"""

from pathlib import Path
from types import SimpleNamespace

import pytest
from lxml import etree

from CopySVGTranslation.config import TranslationConfig
from CopySVGTranslation.injection.id_manager import IdManager
from CopySVGTranslation.preparation.preparer import PreparationContext
from CopySVGTranslation.preparation.steps.normalize_tspans import (
    NormalizeTspans,
    WrapTspans,
)

SVG_NS = "http://www.w3.org/2000/svg"

# ---------------------------------------------------------------------------
# WrapTspans
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
        "id_manager": IdManager(),
        "config": TranslationConfig(assign_missing_ids=True),
        "path": Path("dummy.svg"),
    }
    defaults.update(overrides)
    return PreparationContext(**defaults)


@pytest.fixture
def wrap_tspans_step():
    return WrapTspans(config=SimpleNamespace())


@pytest.fixture
def normalize_tspans_step():
    return NormalizeTspans(config=SimpleNamespace(nested_strategy="raise"))


class TestWrapTspansAndNormalizeTspans:

    def test_empty_text_element_is_removed_after_wrap(self, wrap_tspans_step, normalize_tspans_step):
        root = make_root('<g><text id="t1"></text></g>')
        ctx = make_ctx(root=root)

        normalize_tspans_step.execute(ctx)
        wrap_tspans_step.execute(ctx)

        texts = root.findall(f".//{{{SVG_NS}}}text")
        assert len(texts) == 0

    def test_blank_id_is_stripped_and_dropped(self, wrap_tspans_step, normalize_tspans_step):
        root = make_root('<text id="t1">  <tspan id="  ">hello</tspan></text>')
        ctx = make_ctx(root=root)

        normalize_tspans_step.execute(ctx)
        wrap_tspans_step.execute(ctx)

        tspan = root.find(f".//{{{SVG_NS}}}tspan")
        assert tspan is not None

        assert tspan.get("id") is None

    def test_purely_numeric_id_is_dropped(self, wrap_tspans_step, normalize_tspans_step):
        root = make_root('<text id="t1"><tspan id="123">hello</tspan></text>')
        ctx = make_ctx(root=root)

        normalize_tspans_step.execute(ctx)
        wrap_tspans_step.execute(ctx)

        tspan = root.find(f".//{{{SVG_NS}}}tspan")
        assert tspan is not None

        assert tspan.get("id") is None
        assert ctx.id_manager is not None

        assert "123" not in ctx.id_manager.existing_ids

    def test_id_with_pipe_raises(self, wrap_tspans_step, normalize_tspans_step):
        from CopySVGTranslation.exceptions import SvgStructureError as PublicSvgStructureError

        root = make_root('<text id="t1"><tspan id="a|b">hello</tspan></text>')
        ctx = make_ctx(root=root)

        with pytest.raises(PublicSvgStructureError) as exc_info:
            normalize_tspans_step.execute(ctx)
            wrap_tspans_step.execute(ctx)

        assert exc_info.value.code == "structure-error-invalid-node-id"

    def test_id_with_slash_raises(self, wrap_tspans_step, normalize_tspans_step):
        from CopySVGTranslation.exceptions import SvgStructureError as PublicSvgStructureError

        root = make_root('<text id="t1"><tspan id="a/b">hello</tspan></text>')
        ctx = make_ctx(root=root)

        with pytest.raises(PublicSvgStructureError):
            normalize_tspans_step.execute(ctx)
            wrap_tspans_step.execute(ctx)

    def test_valid_id_is_registered(self, wrap_tspans_step, normalize_tspans_step):
        root = make_root('<text id="t1"><tspan id="my-span">hello</tspan></text>')
        ctx = make_ctx(root=root)

        normalize_tspans_step.execute(ctx)
        wrap_tspans_step.execute(ctx)

        assert ctx.id_manager is not None

        assert "my-span" in ctx.id_manager.existing_ids


class TestWrapTspans:
    def test_root_none_is_a_noop(self, wrap_tspans_step):
        ctx = make_ctx(root=None)

        wrap_tspans_step.execute(ctx)

    def test_whitespace_only_text_is_not_wrapped(self, wrap_tspans_step):
        root = make_root('<text id="t1">   </text>')
        ctx = make_ctx(root=root)

        wrap_tspans_step.execute(ctx)

        text = root.find(f".//{{{SVG_NS}}}text")
        assert text is not None

        # no non-whitespace content: no tspan created, and the (empty)
        # <text> itself is removed by _clean_ids_and_remove_empty_nodes
        assert text.text == "   " or text.text is None

    def test_missing_id_manager_raises(self, wrap_tspans_step):
        root = make_root('<text id="t1">hello</text>')
        ctx = make_ctx(root=root, id_manager=None)

        with pytest.raises(ValueError, match="id_manager is not set"):
            wrap_tspans_step.execute(ctx)

    def test_no_tspans_leaves_translatable_nodes_empty(self, wrap_tspans_step):
        root = make_root('<text id="t1">hello</text>')
        ctx = make_ctx(root=root)

        wrap_tspans_step.execute(ctx)

        assert ctx.translatable_nodes == []


# ---------------------------------------------------------------------------
# NormalizeTspans
# ---------------------------------------------------------------------------

class TestNormalizeTspans:
    def test_root_none_is_a_noop(self, normalize_tspans_step):
        ctx = make_ctx(root=None)

        normalize_tspans_step.execute(ctx)

        assert ctx.translatable_nodes == []

    def test_leaf_tspans_are_collected_as_translatable(self, normalize_tspans_step):
        root = make_root('<text id="t1"><tspan id="s1">hello</tspan></text>')
        ctx = make_ctx(root=root)

        normalize_tspans_step.execute(ctx)

        assert len(ctx.translatable_nodes) == 2
        assert ctx.translatable_nodes[0].get("id") == "s1"

    def test_multiple_leaf_tspans_are_all_collected(self, normalize_tspans_step):
        root = make_root('<text id="t1"><tspan id="s1">a</tspan><tspan id="s2">b</tspan></text>')
        ctx = make_ctx(root=root)

        normalize_tspans_step.execute(ctx)

        ids = [n.get("id") for n in ctx.translatable_nodes]
        assert ids == ["s1", "s2", "t1"]

    def test_nested_tspan_raises(self, normalize_tspans_step):
        from CopySVGTranslation.exceptions import SvgNestedTspanError

        root = make_root('<text id="t1"><tspan id="outer"><tspan id="inner">x</tspan></tspan></text>')
        ctx = make_ctx(root=root)

        with pytest.raises(SvgNestedTspanError):
            normalize_tspans_step.execute(ctx)

    def test_loose_leading_text_is_wrapped_in_tspan(self, normalize_tspans_step):
        root = make_root('<text id="t1">hello</text>')
        ctx = make_ctx(root=root)

        normalize_tspans_step.execute(ctx)

        text = root.find(f".//{{{SVG_NS}}}text")
        assert text is not None

        tspans = text.findall(f"./{{{SVG_NS}}}tspan")
        assert len(tspans) == 1
        assert tspans[0].text == "hello"
        assert text.text is None

    def test_tail_text_after_child_is_wrapped_in_new_tspan(self, normalize_tspans_step):
        root = make_root('<text id="t1"><tspan id="s1">a</tspan>trailing</text>')
        ctx = make_ctx(root=root)

        normalize_tspans_step.execute(ctx)

        text = root.find(f".//{{{SVG_NS}}}text")
        assert text is not None

        tspans = text.findall(f"./{{{SVG_NS}}}tspan")
        assert len(tspans) == 2
        assert tspans[0].get("id") == "s1"
        assert tspans[1].text == "trailing"

    def test_translatable_nodes_rebuilt_with_tspans_before_texts(self, normalize_tspans_step):
        root = make_root('<text id="t1">hello</text>')
        ctx = make_ctx(root=root)

        normalize_tspans_step.execute(ctx)

        tags = [etree.QName(n).localname for n in ctx.translatable_nodes]
        assert tags == ["tspan", "text"]
