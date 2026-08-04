"""
Unit tests for CopySVGTranslation/CopySVGTranslation/preparation/steps/load.py module.

Classes to test: LoadDocument

TODO: write tests
"""

from pathlib import Path
from types import SimpleNamespace

import pytest
from lxml import etree

from CopySVGTranslation.injection.id_manager import IdManager
from CopySVGTranslation.preparation.steps.load import (
    LoadDocument,
)

SVG_NS = "http://www.w3.org/2000/svg"

# ---------------------------------------------------------------------------
# LoadDocument
# ---------------------------------------------------------------------------


def make_root(svg_body: str) -> etree._Element:
    """Build a standalone <svg> root element with the given inner XML."""
    xml = f'<svg xmlns="{SVG_NS}">{svg_body}</svg>'
    return etree.fromstring(xml)


def make_ctx(root: etree._Element | None = None, **overrides) -> SimpleNamespace:
    """Lightweight context stub carrying the attributes these steps read."""
    defaults = {
        "root": root,
        "tree": None,
        "id_manager": IdManager(),
        "translatable_nodes": [],
        "warnings": [],
        "config": SimpleNamespace(assign_missing_ids=True),
        "path": Path("dummy.svg"),
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


@pytest.fixture
def load_step():
    return LoadDocument(config=SimpleNamespace())


class TestLoadDocument:
    def test_execute_delegates_to_svg_document_load(self, load_step, monkeypatch):
        fake_tree = object()
        fake_root = object()

        captured = {}

        class FakeSvgDocument:
            tree = fake_tree
            root = fake_root

        def fake_load(path, config):
            captured["path"] = path
            captured["config"] = config
            return FakeSvgDocument()

        import CopySVGTranslation.preparation.steps.load as load_module

        monkeypatch.setattr(load_module.SvgDocument, "load", staticmethod(fake_load))

        ctx = make_ctx(root=None, path=Path("input.svg"), config=SimpleNamespace(name="cfg"))

        load_step.execute(ctx)

        assert ctx.tree is fake_tree
        assert ctx.root is fake_root
        assert captured["path"] == Path("input.svg")
        assert captured["config"] is ctx.config

    def test_execute_propagates_load_errors(self, load_step, monkeypatch):
        import CopySVGTranslation.preparation.steps.load as load_module

        def fake_load(path, config):
            raise ValueError("bad svg")

        monkeypatch.setattr(load_module.SvgDocument, "load", staticmethod(fake_load))

        ctx = make_ctx(root=None, path=Path("bad.svg"))

        with pytest.raises(ValueError, match="bad svg"):
            load_step.execute(ctx)
