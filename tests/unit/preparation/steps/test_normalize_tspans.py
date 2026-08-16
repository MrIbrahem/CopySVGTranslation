"""
Unit tests for CopySVGTranslation/preparation/steps/normalize_tspans.py module.

Classes to test: NormalizeTspans, AssignIds, RemoveEmptyNodes
"""

from pathlib import Path
from types import SimpleNamespace

import pytest
from lxml import etree

from CopySVGTranslation.config import TranslationConfig
from CopySVGTranslation.injection.id_manager import IdManager
from CopySVGTranslation.preparation.preparer import PreparationContext
from CopySVGTranslation.preparation.steps.normalize_tspans import NormalizeTspans
from CopySVGTranslation.preparation.steps.assign_ids import AssignIds
from CopySVGTranslation.preparation.steps.remove_empty_nodes import RemoveEmptyNodes

SVG_NS = "http://www.w3.org/2000/svg"


def make_root(svg_body: str) -> etree._Element:
    """Build a standalone <svg> root element with the given inner XML."""
    xml = f'<svg xmlns="{SVG_NS}">{svg_body}</svg>'
    return etree.fromstring(xml)


def make_ctx(root: etree._Element | None = None, **overrides) -> PreparationContext:
    """Lightweight context stub carrying the attributes these steps read."""
    defaults = {
        "root": root,
        "tree": None,
        "warnings": [],
        "id_manager": IdManager(),
        "config": TranslationConfig(assign_missing_ids=False),
        "path": Path("dummy.svg"),
    }
    defaults.update(overrides)
    return PreparationContext(**defaults)


@pytest.fixture
def assign_ids_step():
    return AssignIds(config=TranslationConfig(assign_missing_ids=False))


@pytest.fixture
def remove_empty_nodes_step():
    return RemoveEmptyNodes(config=TranslationConfig())


@pytest.fixture
def normalize_tspans_step():
    return NormalizeTspans(config=TranslationConfig(nested_strategy="raise"))


class TestAssignIdsAndRemoveEmptyNodes:

    def test_empty_text_element_is_removed(self, assign_ids_step, remove_empty_nodes_step, normalize_tspans_step):
        root = make_root('<g><text id="t1"></text></g>')
        ctx = make_ctx(root=root)

        normalize_tspans_step.execute(ctx)
        assign_ids_step.execute(ctx)
        remove_empty_nodes_step.execute(ctx)

        texts = root.findall(f".//{{{SVG_NS}}}text")
        assert len(texts) == 0

    def test_blank_id_is_stripped_and_dropped(self, assign_ids_step, remove_empty_nodes_step, normalize_tspans_step):
        root = make_root('<text id="t1">  <tspan id="  ">hello</tspan></text>')
        ctx = make_ctx(root=root)

        normalize_tspans_step.execute(ctx)
        assign_ids_step.execute(ctx)
        remove_empty_nodes_step.execute(ctx)

        tspan = root.find(f".//{{{SVG_NS}}}tspan")
        assert tspan is not None

        assert tspan.get("id") is None

    def test_purely_numeric_id_is_dropped(self, assign_ids_step, remove_empty_nodes_step, normalize_tspans_step):
        root = make_root('<text id="t1"><tspan id="123">hello</tspan></text>')
        ctx = make_ctx(root=root)

        normalize_tspans_step.execute(ctx)
        assign_ids_step.execute(ctx)
        remove_empty_nodes_step.execute(ctx)

        tspan = root.find(f".//{{{SVG_NS}}}tspan")
        assert tspan is not None

        assert tspan.get("id") is None
        assert ctx.id_manager is not None

        assert "123" not in ctx.id_manager.existing_ids

    def test_id_with_pipe_raises(self, assign_ids_step, normalize_tspans_step):
        from CopySVGTranslation.exceptions import SvgStructureError as PublicSvgStructureError

        root = make_root('<text id="t1"><tspan id="a|b">hello</tspan></text>')
        ctx = make_ctx(root=root)

        with pytest.raises(PublicSvgStructureError) as exc_info:
            normalize_tspans_step.execute(ctx)
            assign_ids_step.execute(ctx)

        assert exc_info.value.code == "structure-error-invalid-node-id"

    def test_id_with_slash_raises(self, assign_ids_step, normalize_tspans_step):
        from CopySVGTranslation.exceptions import SvgStructureError as PublicSvgStructureError

        root = make_root('<text id="t1"><tspan id="a/b">hello</tspan></text>')
        ctx = make_ctx(root=root)

        with pytest.raises(PublicSvgStructureError):
            normalize_tspans_step.execute(ctx)
            assign_ids_step.execute(ctx)

    def test_valid_id_is_registered(self, assign_ids_step, remove_empty_nodes_step, normalize_tspans_step):
        root = make_root('<text id="t1"><tspan id="my-span">hello</tspan></text>')
        ctx = make_ctx(root=root)

        normalize_tspans_step.execute(ctx)
        assign_ids_step.execute(ctx)
        remove_empty_nodes_step.execute(ctx)

        assert ctx.id_manager is not None

        assert "my-span" in ctx.id_manager.existing_ids


class TestRemoveEmptyNodes:
    def test_root_none_is_a_noop(self, remove_empty_nodes_step):
        ctx = make_ctx(root=None)

        remove_empty_nodes_step.execute(ctx)

    def test_whitespace_only_text_is_not_wrapped(self, assign_ids_step, remove_empty_nodes_step):
        root = make_root('<text id="t1">   </text>')
        ctx = make_ctx(root=root)

        assign_ids_step.execute(ctx)
        remove_empty_nodes_step.execute(ctx)

        text = root.find(f".//{{{SVG_NS}}}text")
        assert text is not None
        assert text.text == "   " or text.text is None

    def test_missing_id_manager_raises(self, remove_empty_nodes_step):
        root = make_root('<text id="t1">hello</text>')
        ctx = make_ctx(root=root, id_manager=None)

        with pytest.raises(ValueError, match="id_manager is not set"):
            remove_empty_nodes_step.execute(ctx)


# ---------------------------------------------------------------------------
# NormalizeTspans
# ---------------------------------------------------------------------------


class TestNormalizeTspans:

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
