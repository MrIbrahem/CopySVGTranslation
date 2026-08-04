"""
Tests for WrapTextElements._process_text_elements

Unit tests for CopySVGTranslation/preparation/steps/wrap_text_elements.py module.
"""

from types import SimpleNamespace

import pytest
from lxml import etree

from CopySVGTranslation.exceptions import SvgStructureError
from CopySVGTranslation.injection.id_manager import IdManager
from CopySVGTranslation.preparation.steps.wrap_text_elements import SVG_NS, WrapTextElements


class TestSetup:
    def tostring(self, el: etree._Element, pretty_print=False) -> str:
        return etree.tostring(el, pretty_print=pretty_print).decode("utf-8").strip()


# ---------------------------------------------------------------------------
# Shared fixtures/helpers needed for _process_text_elements tests
# ---------------------------------------------------------------------------


@pytest.fixture
def step_factory():
    """
    Factory fixture to build a WrapTextElements instance with a controllable
    `config.normalize_languages` flag, since `_process_text_elements` reads
    it directly and the plain `step` fixture uses config=None (default
    TranslationConfig, whose normalize_languages value we don't want to
    depend on in these tests).
    """

    def _make(normalize_languages: bool) -> WrapTextElements:
        config = SimpleNamespace(normalize_languages=normalize_languages)
        return WrapTextElements(config=config)

    return _make


def make_root(svg_body: str) -> etree._Element:
    """Build a standalone <svg> root element with the given inner XML."""
    xml = f'<svg xmlns="{SVG_NS}">{svg_body}</svg>'
    return etree.fromstring(xml)


def make_ctx(root: etree._Element) -> SimpleNamespace:
    """Lightweight context stub carrying only what _process_text_elements reads."""
    return SimpleNamespace(root=root, id_manager=IdManager())


# ---------------------------------------------------------------------------
# _process_text_elements
# ---------------------------------------------------------------------------


class TestProcessTextElements(TestSetup):

    def test_root_none_is_a_noop(self, step_factory):
        step = step_factory(normalize_languages=False)
        ctx = SimpleNamespace(root=None, id_manager=IdManager())

        # should return immediately without raising
        step._process_text_elements(ctx)

    def test_systemlanguage_normalized_when_config_enabled(self, step_factory):
        step = step_factory(normalize_languages=True)
        root = make_root('<switch><text id="t1" systemLanguage="pt-br">hello</text></switch>')
        ctx = make_ctx(root)

        step._process_text_elements(ctx)

        text = root.find(f".//{{{SVG_NS}}}text")
        assert text is not None
        assert text.get("systemLanguage") == "pt-BR"

        expected_output = '<svg xmlns="http://www.w3.org/2000/svg"><switch><text id="t1" systemLanguage="pt-BR">hello</text></switch></svg>'
        assert self.tostring(root) == expected_output

    def test_systemlanguage_left_untouched_when_config_disabled(self, step_factory):
        step = step_factory(normalize_languages=False)
        root = make_root('<switch><text id="t1" systemLanguage="pt-br">hello</text></switch>')
        ctx = make_ctx(root)

        step._process_text_elements(ctx)

        text = root.find(f".//{{{SVG_NS}}}text")
        assert text is not None
        assert text.get("systemLanguage") == "pt-br"

        expected_output = """<svg xmlns="http://www.w3.org/2000/svg"><switch><text id="t1" systemLanguage="pt-br">hello</text></switch></svg>"""
        assert self.tostring(root) == expected_output

    def test_already_normalized_language_is_unaffected(self, step_factory):
        step = step_factory(normalize_languages=True)
        root = make_root('<switch><text id="t1" systemLanguage="ar">hello</text></switch>')
        ctx = make_ctx(root)

        step._process_text_elements(ctx)

        text = root.find(f".//{{{SVG_NS}}}text")
        assert text is not None
        assert text.get("systemLanguage") == "ar"

        expected_output = """<svg xmlns="http://www.w3.org/2000/svg"><switch><text id="t1" systemLanguage="ar">hello</text></switch></svg>"""
        assert self.tostring(root) == expected_output

    def test_text_without_switch_parent_gets_wrapped_in_new_switch(self, step_factory):
        step = step_factory(normalize_languages=False)
        root = make_root('<g><text id="t1">hello</text></g>')
        ctx = make_ctx(root)

        step._process_text_elements(ctx)

        g = root.find(f".//{{{SVG_NS}}}g")
        children = list(g)
        assert len(children) == 1

        switch = children[0]
        assert switch.tag == f"{{{SVG_NS}}}switch"

        switch_children = list(switch)
        assert len(switch_children) == 1
        assert switch_children[0].get("id") == "t1"

        expected_output = (
            """<svg xmlns="http://www.w3.org/2000/svg"><g><switch><text id="t1">hello</text></switch></g></svg>"""
        )
        assert self.tostring(root) == expected_output

    def test_text_already_inside_switch_is_not_rewrapped(self, step_factory):
        step = step_factory(normalize_languages=False)
        root = make_root('<switch><text id="t1">hello</text></switch>')
        ctx = make_ctx(root)

        step._process_text_elements(ctx)

        switches = root.findall(f".//{{{SVG_NS}}}switch")
        assert len(switches) == 1
        assert list(switches[0])[0].get("id") == "t1"

        expected_output = (
            """<svg xmlns="http://www.w3.org/2000/svg"><switch><text id="t1">hello</text></switch></svg>"""
        )
        assert self.tostring(root) == expected_output

    def test_new_switch_is_inserted_at_original_text_position(self, step_factory):
        step = step_factory(normalize_languages=False)
        root = make_root('<g><rect id="before"/><text id="t1">hello</text><rect id="after"/></g>')
        ctx = make_ctx(root)

        step._process_text_elements(ctx)

        g = root.find(f".//{{{SVG_NS}}}g")
        children = list(g)
        tags = ["switch" if c.tag == f"{{{SVG_NS}}}switch" else c.get("id") for c in children]
        assert tags == ["before", "switch", "after"]

        expected_output = """<svg xmlns="http://www.w3.org/2000/svg"><g><rect id="before"/><switch><text id="t1">hello</text></switch><rect id="after"/></g></svg>"""
        assert self.tostring(root) == expected_output

    def test_style_attribute_is_copied_from_text_to_new_switch(self, step_factory):
        step = step_factory(normalize_languages=False)
        root = make_root('<g><text id="t1" style="fill:red">hello</text></g>')
        ctx = make_ctx(root)

        step._process_text_elements(ctx)

        text = root.find(f".//{{{SVG_NS}}}text")
        assert text is not None

        switch = text.getparent()
        assert switch is not None

        assert switch.tag == f"{{{SVG_NS}}}switch"
        assert switch.get("style") == "fill:red"
        # note: the style attribute is copied to the switch, not removed
        # from the original <text> element
        assert text.get("style") == "fill:red"

        expected_output = """<svg xmlns="http://www.w3.org/2000/svg"><g><switch style="fill:red"><text id="t1" style="fill:red">hello</text></switch></g></svg>"""
        assert self.tostring(root) == expected_output

    def test_style_attribute_is_copied_to_existing_switch_parent(self, step_factory):
        step = step_factory(normalize_languages=False)
        root = make_root('<switch><text id="t1" style="fill:blue">hello</text></switch>')
        ctx = make_ctx(root)

        step._process_text_elements(ctx)

        switch = root.find(f".//{{{SVG_NS}}}switch")
        assert switch is not None
        assert switch.get("style") == "fill:blue"

        expected_output = """<svg xmlns="http://www.w3.org/2000/svg"><switch style="fill:blue"><text id="t1" style="fill:blue">hello</text></switch></svg>"""
        assert self.tostring(root) == expected_output

    def test_no_style_attribute_means_switch_gets_no_style(self, step_factory):
        step = step_factory(normalize_languages=False)
        root = make_root('<text id="t1">hello</text>')
        ctx = make_ctx(root)

        step._process_text_elements(ctx)

        text = root.find(f".//{{{SVG_NS}}}text")
        assert text is not None

        switch = text.getparent()
        assert switch is not None

        assert switch.get("style") is None

        expected_output = (
            """<svg xmlns="http://www.w3.org/2000/svg"><switch><text id="t1">hello</text></switch></svg>"""
        )
        assert self.tostring(root) == expected_output

    def test_tspan_children_are_allowed(self, step_factory):
        step = step_factory(normalize_languages=False)
        root = make_root('<text id="t1"><tspan>hello</tspan><tspan>world</tspan></text>')
        ctx = make_ctx(root)

        # should not raise
        step._process_text_elements(ctx)

        expected_output = """<svg xmlns="http://www.w3.org/2000/svg"><switch><text id="t1"><tspan>hello</tspan><tspan>world</tspan></text></switch></svg>"""
        assert self.tostring(root) == expected_output

    def test_multiple_text_elements_are_each_processed_independently(self, step_factory):
        step = step_factory(normalize_languages=False)
        root = make_root('<g><text id="t1">a</text></g><g><text id="t2">b</text></g>')
        ctx = make_ctx(root)

        step._process_text_elements(ctx)

        switches = root.findall(f".//{{{SVG_NS}}}switch")
        assert len(switches) == 2
        assert list(switches[0])[0].get("id") == "t1"
        assert list(switches[1])[0].get("id") == "t2"

        expected_output = """<svg xmlns="http://www.w3.org/2000/svg"><g><switch><text id="t1">a</text></switch></g><g><switch><text id="t2">b</text></switch></g></svg>"""
        assert self.tostring(root) == expected_output


class TestProcessTextElementsErrors(TestSetup):
    def test_dollar_placeholder_raises(self, step_factory):
        step = step_factory(normalize_languages=False)
        root = make_root('<text id="t1">Hello $1 world</text>')
        ctx = make_ctx(root)

        with pytest.raises(SvgStructureError) as exc_info:
            step._process_text_elements(ctx)

        assert exc_info.value.args[0] == "structure-error-text-contains-dollar"

    def test_dollar_placeholder_detected_inside_nested_tspan(self, step_factory):
        # get_text_content uses itertext(), so the check must see text
        # nested inside child <tspan> elements too, not just direct text.
        step = step_factory(normalize_languages=False)
        root = make_root('<text id="t1"><tspan>Hello $2</tspan></text>')
        ctx = make_ctx(root)

        with pytest.raises(SvgStructureError) as exc_info:
            step._process_text_elements(ctx)

        assert exc_info.value.args[0] == "structure-error-text-contains-dollar"

    def test_dollar_check_takes_priority_over_tspan_check(self, step_factory):
        # A non-tspan child that also contains "$1" should raise the dollar
        # error, since that check runs before the tspan-children check.
        step = step_factory(normalize_languages=False)
        root = make_root('<text id="t1"><a>$1</a></text>')
        ctx = make_ctx(root)

        with pytest.raises(SvgStructureError) as exc_info:
            step._process_text_elements(ctx)

        assert exc_info.value.args[0] == "structure-error-text-contains-dollar"

    def test_no_parent_raises_structure_error(self, step_factory):
        # This branch is normally unreachable through findall() on a real
        # tree, since any element returned by findall() is by definition a
        # descendant and therefore already has a parent. We exercise it by
        # stubbing ctx.root with a fake object whose findall() returns an
        # orphan element (no parent) directly.
        step = step_factory(normalize_languages=False)

        orphan_text = etree.fromstring(f'<text xmlns="{SVG_NS}" id="orphan">hi</text>')
        assert orphan_text.getparent() is None

        fake_root = SimpleNamespace(findall=lambda _pattern: [orphan_text])
        ctx = SimpleNamespace(root=fake_root, id_manager=IdManager())

        with pytest.raises(SvgStructureError) as exc_info:
            step._process_text_elements(ctx)

        assert exc_info.value.args[0] == "structure-error-no-parent-for-text"

    def test_non_tspan_child_raises(self, step_factory):
        step = step_factory(normalize_languages=False)
        root = make_root('<text id="t1"><a>hello</a></text>')
        ctx = make_ctx(root)

        with pytest.raises(SvgStructureError) as exc_info:
            step._process_text_elements(ctx)

        assert exc_info.value.args[0] == "structure-error-non-tspan-inside-text"
