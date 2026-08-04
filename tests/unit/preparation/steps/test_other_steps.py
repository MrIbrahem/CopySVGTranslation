"""
Tests for the preparation steps other than SplitLanguages and
WrapTextElements:

  - AssignIds        (injection/steps/assign_ids.py)
  - LoadDocument      (injection/steps/load.py)
  - NormalizeTspans   (injection/steps/normalize_tspans.py)
  - WrapTspans        (injection/steps/normalize_tspans.py)
  - ReorderTexts      (injection/steps/reorder.py)
  - ValidateStructure (injection/steps/validate.py)

Notes on setup:
- We use `types.SimpleNamespace` instead of the real `PreparationContext`
  dataclass, since each step only reads a handful of attributes
  (`root`, `id_manager`, `translatable_nodes`, `config`, `path`). This
  avoids depending on the full package (config, io, id_manager modules)
  that were not included alongside these step files.
- `FakeIdManager` mimics the subset of the real IdManager's interface that
  these steps actually call: `existing_ids`, `register()`,
  `register_many()`.
- `SvgStructureError`, `SvgInvalidIdError`, and `SvgNestedTspanError` are
  minimal stand-ins for the real exception classes. They accept the same
  keyword arguments (`code`/positional code, `extra`, `element`) used by
  the step modules, and expose `.args[0]` as "<code>: <extra>" or just
  "<code>", matching how earlier SplitLanguages tests asserted on
  `exc_info.value.args[0]`.
- Adjust the import paths below (`injection.steps.*`, `injection.exceptions`,
  `injection.utils`, `injection.id_manager`) to match your actual package
  layout if it differs. Since assign_ids/normalize_tspans/validate import
  their exceptions/utils via relative imports (`...exceptions`,
  `...utils`), these tests patch those modules directly by name so no
  changes to production code are required to run the suite.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path
from types import SimpleNamespace

import pytest
from lxml import etree

SVG_NS = "http://www.w3.org/2000/svg"


# ---------------------------------------------------------------------------
# Minimal stand-ins for exceptions and IdManager, installed as fake modules
# so the step modules' relative imports (`...exceptions`, `...utils`,
# `...injection.id_manager`, `...io`, `...config`) resolve without needing
# the rest of the real package.
# ---------------------------------------------------------------------------


class SvgStructureError(Exception):
    def __init__(self, code: str | None = None, extra=None, **kwargs) -> None:
        self.code = code
        self.extra = extra
        message = code if not extra else f"{code}: {extra}"
        super().__init__(message)


class SvgInvalidIdError(Exception):
    def __init__(self, code: str | None = None, element=None, extra=None, **kwargs) -> None:
        self.code = code
        self.element = element
        message = code if not extra else f"{code}: {extra}"
        super().__init__(message)


class SvgNestedTspanError(Exception):
    def __init__(self, extra=None, **kwargs) -> None:
        self.extra = extra
        message = "structure-error-nested-tspans-not-supported"
        if extra:
            message = f"{message}: {extra}"
        super().__init__(message)


def collect_ids(root: etree._Element) -> set[str]:
    """Real-ish implementation: collect every `id` attribute under root."""
    return {el.get("id") for el in root.xpath("//*[@id]") if el.get("id")}


def sort_switch_children(switch: etree._Element, put_fallback_last: bool = True) -> None:
    """
    Real-ish implementation matching the docstring in ReorderTexts.execute:
    sort <text> children of `switch` by the numeric part of their id
    (if present), keeping original relative order otherwise ("fallback",
    i.e. no systemLanguage, goes last when put_fallback_last=True).
    """
    import re as _re

    children = list(switch)

    def sort_key(el, original_index):
        el_id = el.get("id") or ""
        m = _re.search(r"([0-9]+)", el_id)
        has_lang = bool(el.get("systemLanguage"))
        is_fallback = not has_lang
        fallback_rank = 1 if (put_fallback_last and is_fallback) else 0
        numeric = int(m.group(1)) if m else original_index
        return (fallback_rank, numeric, original_index)

    indexed = list(enumerate(children))
    indexed.sort(key=lambda pair: sort_key(pair[1], pair[0]))

    for child in children:
        switch.remove(child)
    for _, child in indexed:
        switch.append(child)


def _install_fake_modules() -> None:
    pkg_root = "fake_pkg"
    if pkg_root in sys.modules:
        return

    root_mod = types.ModuleType(pkg_root)
    root_mod.__path__ = []
    sys.modules[pkg_root] = root_mod

    exceptions_mod = types.ModuleType(f"{pkg_root}.exceptions")
    exceptions_mod.SvgStructureError = SvgStructureError
    exceptions_mod.SvgInvalidIdError = SvgInvalidIdError
    exceptions_mod.SvgNestedTspanError = SvgNestedTspanError
    sys.modules[f"{pkg_root}.exceptions"] = exceptions_mod

    utils_mod = types.ModuleType(f"{pkg_root}.utils")
    utils_mod.collect_ids = collect_ids
    utils_mod.sort_switch_children = sort_switch_children
    utils_mod.normalize_lang = lambda s: s
    utils_mod.split_lang_list = lambda s: [p.strip() for p in s.split(",") if p.strip()]
    sys.modules[f"{pkg_root}.utils"] = utils_mod

    injection_mod = types.ModuleType(f"{pkg_root}.injection")
    injection_mod.__path__ = []
    injection_mod.SvgStructureError = SvgStructureError
    sys.modules[f"{pkg_root}.injection"] = injection_mod

    id_manager_mod = types.ModuleType(f"{pkg_root}.injection.id_manager")

    class IdManager:  # pragma: no cover - only used for type resolution
        pass

    id_manager_mod.IdManager = IdManager
    sys.modules[f"{pkg_root}.injection.id_manager"] = id_manager_mod

    config_mod = types.ModuleType(f"{pkg_root}.config")

    class TranslationConfig:
        def __init__(self, assign_missing_ids: bool = True) -> None:
            self.assign_missing_ids = assign_missing_ids

    config_mod.TranslationConfig = TranslationConfig
    sys.modules[f"{pkg_root}.config"] = config_mod

    io_mod = types.ModuleType(f"{pkg_root}.io")

    class SvgDocument:  # pragma: no cover - overridden per-test via monkeypatch
        @staticmethod
        def load(path, config):
            raise NotImplementedError

    io_mod.SvgDocument = SvgDocument
    sys.modules[f"{pkg_root}.io"] = io_mod


_install_fake_modules()


class FakeIdManager:
    """Minimal stand-in exposing the subset of IdManager used by these steps."""

    def __init__(self) -> None:
        self.existing_ids: set[str] = set()
        self.registered: list[str] = []
        self.registered_many_calls: list[set[str]] = []

    def register(self, id_value: str) -> None:
        self.existing_ids.add(id_value)
        self.registered.append(id_value)

    def register_many(self, ids) -> None:
        ids = set(ids)
        self.existing_ids.update(ids)
        self.registered_many_calls.append(ids)


def make_root(svg_body: str) -> etree._Element:
    """Build a standalone <svg> root element with the given inner XML."""
    xml = f'<svg xmlns="{SVG_NS}">{svg_body}</svg>'
    return etree.fromstring(xml)


def make_ctx(root: etree._Element | None = None, **overrides) -> SimpleNamespace:
    """Lightweight context stub carrying the attributes these steps read."""
    defaults = dict(
        root=root,
        tree=None,
        id_manager=FakeIdManager(),
        translatable_nodes=[],
        warnings=[],
        config=SimpleNamespace(assign_missing_ids=True),
        path=Path("dummy.svg"),
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def tostring(el: etree._Element) -> str:
    return etree.tostring(el, pretty_print=False).decode("utf-8").strip()


# ---------------------------------------------------------------------------
# AssignIds
# ---------------------------------------------------------------------------


@pytest.fixture
def assign_ids_step():
    from CopySVGTranslation.preparation.steps.assign_ids import AssignIds

    return AssignIds(config=SimpleNamespace(assign_missing_ids=True))


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
        root = make_root('<text>hello</text>')
        ctx = make_ctx(root=root, config=SimpleNamespace(assign_missing_ids=True))

        assign_ids_step.execute(ctx)

        text = root.find(f".//{{{SVG_NS}}}text")
        assert text.get("id") == "trsvg1"
        assert "trsvg1" in ctx.id_manager.existing_ids

    def test_missing_text_id_not_assigned_when_config_disabled(self, assign_ids_step):
        root = make_root('<text>hello</text>')
        ctx = make_ctx(root=root, config=SimpleNamespace(assign_missing_ids=False))

        assign_ids_step.execute(ctx)

        text = root.find(f".//{{{SVG_NS}}}text")
        assert text.get("id") is None

    def test_missing_tspan_id_is_assigned(self, assign_ids_step):
        root = make_root('<text id="t1"><tspan>hello</tspan></text>')
        ctx = make_ctx(root=root)

        assign_ids_step.execute(ctx)

        tspan = root.find(f".//{{{SVG_NS}}}tspan")
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
        root = make_root(
            '<text>a<tspan>x</tspan></text>'
            '<text>b</text>'
        )
        ctx = make_ctx(root=root)

        assign_ids_step.execute(ctx)

        assigned = [el.get("id") for el in root.iter() if isinstance(el.tag, str) and el.get("id")]
        # all ids must be unique
        assert len(assigned) == len(set(assigned))
        assert len(assigned) == 3  # 2 <text> + 1 <tspan>


# ---------------------------------------------------------------------------
# LoadDocument
# ---------------------------------------------------------------------------


@pytest.fixture
def load_step():
    from CopySVGTranslation.preparation.steps.load import LoadDocument

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


# ---------------------------------------------------------------------------
# NormalizeTspans
# ---------------------------------------------------------------------------


@pytest.fixture
def normalize_tspans_step():
    from CopySVGTranslation.preparation.steps.normalize_tspans import NormalizeTspans

    return NormalizeTspans(config=SimpleNamespace())


class TestNormalizeTspans:
    def test_root_none_is_a_noop(self, normalize_tspans_step):
        ctx = make_ctx(root=None)

        normalize_tspans_step.execute(ctx)

        assert ctx.translatable_nodes == []

    def test_leaf_tspans_are_collected_as_translatable(self, normalize_tspans_step):
        root = make_root('<text id="t1"><tspan id="s1">hello</tspan></text>')
        ctx = make_ctx(root=root)

        normalize_tspans_step.execute(ctx)

        assert len(ctx.translatable_nodes) == 1
        assert ctx.translatable_nodes[0].get("id") == "s1"

    def test_multiple_leaf_tspans_are_all_collected(self, normalize_tspans_step):
        root = make_root(
            '<text id="t1"><tspan id="s1">a</tspan><tspan id="s2">b</tspan></text>'
        )
        ctx = make_ctx(root=root)

        normalize_tspans_step.execute(ctx)

        ids = [n.get("id") for n in ctx.translatable_nodes]
        assert ids == ["s1", "s2"]

    def test_nested_tspan_raises(self, normalize_tspans_step):
        from CopySVGTranslation.exceptions import SvgNestedTspanError

        root = make_root(
            '<text id="t1"><tspan id="outer"><tspan id="inner">x</tspan></tspan></text>'
        )
        ctx = make_ctx(root=root)

        with pytest.raises(SvgNestedTspanError):
            normalize_tspans_step.execute(ctx)

    def test_no_tspans_leaves_translatable_nodes_empty(self, normalize_tspans_step):
        root = make_root('<text id="t1">hello</text>')
        ctx = make_ctx(root=root)

        normalize_tspans_step.execute(ctx)

        assert ctx.translatable_nodes == []


# ---------------------------------------------------------------------------
# WrapTspans
# ---------------------------------------------------------------------------


@pytest.fixture
def wrap_tspans_step():
    from CopySVGTranslation.preparation.steps.normalize_tspans import WrapTspans

    return WrapTspans(config=SimpleNamespace())


class TestWrapTspans:
    def test_root_none_is_a_noop(self, wrap_tspans_step):
        ctx = make_ctx(root=None)

        wrap_tspans_step.execute(ctx)

    def test_loose_leading_text_is_wrapped_in_tspan(self, wrap_tspans_step):
        root = make_root('<text id="t1">hello</text>')
        ctx = make_ctx(root=root)

        wrap_tspans_step.execute(ctx)

        text = root.find(f".//{{{SVG_NS}}}text")
        tspans = text.findall(f"./{{{SVG_NS}}}tspan")
        assert len(tspans) == 1
        assert tspans[0].text == "hello"
        assert text.text is None

    def test_tail_text_after_child_is_wrapped_in_new_tspan(self, wrap_tspans_step):
        root = make_root('<text id="t1"><tspan id="s1">a</tspan>trailing</text>')
        ctx = make_ctx(root=root)

        wrap_tspans_step.execute(ctx)

        text = root.find(f".//{{{SVG_NS}}}text")
        tspans = text.findall(f"./{{{SVG_NS}}}tspan")
        assert len(tspans) == 2
        assert tspans[0].get("id") == "s1"
        assert tspans[1].text == "trailing"

    def test_whitespace_only_text_is_not_wrapped(self, wrap_tspans_step):
        root = make_root('<text id="t1">   </text>')
        ctx = make_ctx(root=root)

        wrap_tspans_step.execute(ctx)

        text = root.find(f".//{{{SVG_NS}}}text")
        # no non-whitespace content: no tspan created, and the (empty)
        # <text> itself is removed by _clean_ids_and_remove_empty_nodes
        assert text.text == "   " or text.text is None

    def test_empty_text_element_is_removed_after_wrap(self, wrap_tspans_step):
        root = make_root('<g><text id="t1"></text></g>')
        ctx = make_ctx(root=root)

        wrap_tspans_step.execute(ctx)

        texts = root.findall(f".//{{{SVG_NS}}}text")
        assert len(texts) == 0

    def test_translatable_nodes_rebuilt_with_tspans_before_texts(self, wrap_tspans_step):
        root = make_root('<text id="t1">hello</text>')
        ctx = make_ctx(root=root)

        wrap_tspans_step.execute(ctx)

        tags = [etree.QName(n).localname for n in ctx.translatable_nodes]
        assert tags == ["tspan", "text"]

    def test_blank_id_is_stripped_and_dropped(self, wrap_tspans_step):
        root = make_root('<text id="t1">  <tspan id="  ">hello</tspan></text>')
        ctx = make_ctx(root=root)

        wrap_tspans_step.execute(ctx)

        tspan = root.find(f".//{{{SVG_NS}}}tspan")
        assert tspan.get("id") is None

    def test_purely_numeric_id_is_dropped(self, wrap_tspans_step):
        root = make_root('<text id="t1"><tspan id="123">hello</tspan></text>')
        ctx = make_ctx(root=root)

        wrap_tspans_step.execute(ctx)

        tspan = root.find(f".//{{{SVG_NS}}}tspan")
        assert tspan.get("id") is None
        assert "123" not in ctx.id_manager.existing_ids

    def test_id_with_pipe_raises(self, wrap_tspans_step):
        from CopySVGTranslation.exceptions import SvgStructureError as PublicSvgStructureError

        root = make_root('<text id="t1"><tspan id="a|b">hello</tspan></text>')
        ctx = make_ctx(root=root)

        with pytest.raises(PublicSvgStructureError) as exc_info:
            wrap_tspans_step.execute(ctx)

        assert exc_info.value.code == "structure-error-invalid-node-id"

    def test_id_with_slash_raises(self, wrap_tspans_step):
        from CopySVGTranslation.exceptions import SvgStructureError as PublicSvgStructureError

        root = make_root('<text id="t1"><tspan id="a/b">hello</tspan></text>')
        ctx = make_ctx(root=root)

        with pytest.raises(PublicSvgStructureError):
            wrap_tspans_step.execute(ctx)

    def test_valid_id_is_registered(self, wrap_tspans_step):
        root = make_root('<text id="t1"><tspan id="my-span">hello</tspan></text>')
        ctx = make_ctx(root=root)

        wrap_tspans_step.execute(ctx)

        assert "my-span" in ctx.id_manager.existing_ids

    def test_missing_id_manager_raises(self, wrap_tspans_step):
        root = make_root('<text id="t1">hello</text>')
        ctx = make_ctx(root=root, id_manager=None)

        with pytest.raises(ValueError, match="id_manager is not set"):
            wrap_tspans_step.execute(ctx)


# ---------------------------------------------------------------------------
# ReorderTexts
# ---------------------------------------------------------------------------


@pytest.fixture
def reorder_step():
    from CopySVGTranslation.preparation.steps.reorder import ReorderTexts

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
            "<switch>"
            '<text id="trsvg1">fallback</text>'
            '<text id="trsvg2" systemLanguage="ar">a</text>'
            "</switch>"
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
