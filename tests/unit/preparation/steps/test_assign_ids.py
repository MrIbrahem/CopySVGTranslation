"""
Unit tests for CopySVGTranslation/CopySVGTranslation/preparation/steps/assign_ids.py module.

Classes to test: AssignIds

"""

from pathlib import Path
from types import SimpleNamespace

import pytest
from lxml import etree

from CopySVGTranslation.config import TranslationConfig
from CopySVGTranslation.injection.id_manager import IdManager
from CopySVGTranslation.preparation.preparer import PreparationContext
from CopySVGTranslation.preparation.steps.assign_ids import (
    AssignIds,
)

SVG_NS = "http://www.w3.org/2000/svg"


# ---------------------------------------------------------------------------
# AssignIds
# ---------------------------------------------------------------------------


@pytest.fixture
def assign_ids_step():
    return AssignIds(config=SimpleNamespace(assign_missing_ids=True))


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


class TestAssignIds:
    def test_root_none_is_a_noop(self, assign_ids_step):
        ctx = make_ctx(root=None)

        # should return immediately without raising, even with no id_manager
        assign_ids_step.execute(ctx)

    def test_missing_id_manager_raises(self, assign_ids_step):
        root = make_root('<text id="t1">hello</text>')
        ctx = make_ctx(root=root, id_manager=None)

        with pytest.raises(Exception, match="ID manager is not initialized"):
            assign_ids_step.execute(ctx)

    def test_existing_ids_are_registered(self, assign_ids_step):
        root = make_root('<text id="t1"><tspan id="s1">hello</tspan></text>')
        ctx = make_ctx(root=root)

        assign_ids_step.execute(ctx)

        assert ctx.id_manager.existing_ids == {"t1", "s1"}

    def test_blank_existing_id_raises_invalid_id_error(self, assign_ids_step):
        from CopySVGTranslation.exceptions import SvgInvalidIdError

        root = make_root('<text id="  ">hello</text>')
        ctx = make_ctx(root=root)

        with pytest.raises(SvgInvalidIdError) as exc_info:
            assign_ids_step.execute(ctx)

        assert exc_info.value.code == "structure-error-invalid-node-id"

    def test_missing_text_id_is_assigned_when_config_enabled(self, assign_ids_step):
        root = make_root("<text>hello</text>")
        ctx = make_ctx(root=root, config=SimpleNamespace(assign_missing_ids=True))

        assign_ids_step.execute(ctx)

        text = root.find(f".//{{{SVG_NS}}}text")
        assert text is not None

        assert text.get("id") == "trsvg1"
        assert "trsvg1" in ctx.id_manager.existing_ids

    def test_missing_text_id_not_assigned_when_config_disabled(self, assign_ids_step):
        root = make_root("<text>hello</text>")
        ctx = make_ctx(root=root)
        ctx.config = SimpleNamespace(assign_missing_ids=False)

        assign_ids_step.execute(ctx)

        text = root.find(f".//{{{SVG_NS}}}text")
        assert text is not None

        assert text.get("id") == "trsvg1"
        assert text.get("id") is None

    def test_missing_tspan_id_is_assigned(self, assign_ids_step):
        root = make_root('<text id="t1"><tspan>hello</tspan></text>')
        ctx = make_ctx(root=root)

        assign_ids_step.execute(ctx)

        tspan = root.find(f".//{{{SVG_NS}}}tspan")
        assert tspan is not None

        assert tspan.get("id") == "trsvg1"

    def test_new_ids_skip_already_registered_trsvg_numbers(self, assign_ids_step):
        # trsvg1 is already taken by an existing element, so the newly
        # assigned id for the id-less <text> must skip past it.
        root = make_root('<text id="trsvg1">a</text><text>b</text>')
        ctx = make_ctx(root=root)

        assign_ids_step.execute(ctx)

        texts = root.findall(f".//{{{SVG_NS}}}text")
        assert texts[0].get("id") == "trsvg1"
        assert texts[1].get("id") == "trsvg2"

    def test_multiple_missing_ids_each_get_unique_trsvg_ids(self, assign_ids_step):
        root = make_root("<text>a<tspan>x</tspan></text><text>b</text>")
        ctx = make_ctx(root=root)

        assign_ids_step.execute(ctx)

        assigned = [el.get("id") for el in root.iter() if isinstance(el.tag, str) and el.get("id")]
        # all ids must be unique
        assert len(assigned) == len(set(assigned))
        assert len(assigned) == 3  # 2 <text> + 1 <tspan>
