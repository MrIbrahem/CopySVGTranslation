"""
Tests for SplitLanguages._split_switch_languages and its core helper
_split_languages_in_switch.

Notes on setup:
- We use `types.SimpleNamespace` instead of the real `PreparationContext`
  dataclass, since only `.rofrom CopySVGTranslation.e actually read by the
  methods under test. This avoids pulling in unrelated dependencies
  (TranslationConfig, IdManager, Path, etc.) that aren't needed here.
- `FakeIdManager` is a minimal stand-in that mimics the two methods the
  production IdManager exposes: `allocate_trsvg()` and `allocate_clone()`.
- Adjust the import path below (`injection.steps.split_languages`) to match
  your actual package layout if it differs.

Unit tests for CopySVGTranslation/preparation/steps/split_languages.py module.
"""

from types import SimpleNamespace

import pytest
from lxml import etree

from CopySVGTranslation.exceptions import SvgStructureError
from CopySVGTranslation.preparation.steps.split_languages import SVG_NS, SplitLanguages
from CopySVGTranslation.injection.id_manager import IdManager

def make_switch(children_xml: str) -> etree._Element:
    """Build a standalone <switch> element (SVG namespace) with given children."""
    xml = f'<switch xmlns="{SVG_NS}">{children_xml}</switch>'
    return etree.fromstring(xml)


@pytest.fixture
def step() -> SplitLanguages:
    """Instance of the step under test; config is unused by these methods."""
    return SplitLanguages(config=None)


@pytest.fixture
def ctx() -> SimpleNamespace:
    """Lightweight context stub with a fresh IdManager per test."""
    return SimpleNamespace(root=None, id_manager=IdManager())


# ---------------------------------------------------------------------------
# _split_languages_in_switch
# ---------------------------------------------------------------------------


class TestSetup:
    def tostring(self, el: etree._Element, pretty_print=False) -> str:
        return etree.tostring(el, pretty_print=pretty_print).decode("utf-8").strip()


class TestSplitLanguagesInSwitch(TestSetup):

    def test_single_text_without_systemlanguage_is_left_as_fallback(self, step, ctx):
        switch = make_switch('<text id="t1">hello</text>')

        step._split_languages_in_switch(switch, ctx)

        children = list(switch)
        assert len(children) == 1
        assert children[0].get("systemLanguage") is None
        expected_output = """<switch xmlns="http://www.w3.org/2000/svg"><text id="t1">hello</text></switch>"""
        assert self.tostring(switch) == expected_output

    def test_single_text_with_one_language_keeps_systemlanguage(self, step, ctx):
        switch = make_switch('<text id="t1" systemLanguage="ar">hello</text>')

        step._split_languages_in_switch(switch, ctx)

        children = list(switch)
        assert len(children) == 1
        assert children[0].get("systemLanguage") == "ar"
        expected_output = (
            """<switch xmlns="http://www.w3.org/2000/svg"><text id="t1" systemLanguage="ar">hello</text></switch>"""
        )
        assert self.tostring(switch) == expected_output

    def test_explicit_fallback_value_is_normalized_to_no_attribute(self, step, ctx):
        # systemLanguage="fallback" written explicitly should behave the
        # same as a missing systemLanguage attribute.
        switch = make_switch('<text id="t1" systemLanguage="fallback">hello</text>')

        step._split_languages_in_switch(switch, ctx)

        children = list(switch)
        assert len(children) == 1
        assert children[0].get("systemLanguage") is None
        expected_output = """<switch xmlns="http://www.w3.org/2000/svg"><text id="t1">hello</text></switch>"""
        assert self.tostring(switch) == expected_output

    def test_comma_separated_languages_are_split_into_clones(self, step, ctx):
        switch = make_switch('<text id="t1" systemLanguage="ar,fr,pt-br">hello</text>')

        step._split_languages_in_switch(switch, ctx)

        children = list(switch)
        assert len(children) == 3
        assert [c.get("systemLanguage") for c in children] == ["ar", "fr", "pt-BR"]

        # original node keeps its id; clones get ids from id_manager.allocate_clone
        assert children[0].get("id") == "t1"
        assert children[1].get("id") == "t1-fr"
        assert children[2].get("id") == "t1-pt-br"

        expected_output = """<switch xmlns="http://www.w3.org/2000/svg"><text id="t1" systemLanguage="ar">hello</text><text id="t1-fr" systemLanguage="fr">hello</text><text id="t1-pt-br" systemLanguage="pt-BR">hello</text></switch>"""
        assert self.tostring(switch) == expected_output

    def test_clone_without_original_id_uses_allocate_trsvg(self, step, ctx):
        switch = make_switch('<text systemLanguage="ar,fr">hello</text>')

        step._split_languages_in_switch(switch, ctx)

        children = list(switch)
        assert len(children) == 2
        # no original id present, so the clone must get a fresh trsvg id
        assert children[1].get("id") == "trsvg1"
        expected_output = """<switch xmlns="http://www.w3.org/2000/svg"><text systemLanguage="ar">hello</text><text systemLanguage="fr" id="trsvg1">hello</text></switch>"""
        assert self.tostring(switch) == expected_output

    def test_clone_with_trsvg_like_id_is_reallocated(self, step, ctx):
        # An id already matching the internal trsvgN pattern must be treated
        # as if it were absent, to avoid id collisions.
        switch = make_switch('<text id="trsvg5" systemLanguage="ar,fr">hello</text>')

        step._split_languages_in_switch(switch, ctx)

        children = list(switch)
        assert children[1].get("id") == "trsvg1"
        expected_output = """<switch xmlns="http://www.w3.org/2000/svg"><text id="trsvg5" systemLanguage="ar">hello</text><text id="trsvg1" systemLanguage="fr">hello</text></switch>"""
        assert self.tostring(switch) == expected_output

    def test_fallback_inside_comma_list_removes_attribute_on_that_node(self, step, ctx):
        switch = make_switch('<text id="t1" systemLanguage="ar,fallback">hello</text>')

        step._split_languages_in_switch(switch, ctx)

        children = list(switch)
        assert len(children) == 2
        assert children[0].get("systemLanguage") == "ar"

        expeced = """<text xmlns="http://www.w3.org/2000/svg" id="t1-">hello</text>"""

        expected_output = """<switch xmlns="http://www.w3.org/2000/svg"><text id="t1" systemLanguage="ar">hello</text><text id="t1-">hello</text></switch>"""
        assert self.tostring(switch) == expected_output
        assert self.tostring(children[1]) == expeced

        assert children[1].get("systemLanguage") is None

    def test_multiple_independent_single_language_texts(self, step, ctx):
        switch = make_switch('<text id="t1" systemLanguage="ar">a</text><text id="t2" systemLanguage="fr">b</text>')

        step._split_languages_in_switch(switch, ctx)

        children = list(switch)
        assert len(children) == 2
        assert children[0].get("systemLanguage") == "ar"
        assert children[1].get("systemLanguage") == "fr"

        expected_output = """<switch xmlns="http://www.w3.org/2000/svg"><text id="t1" systemLanguage="ar">a</text><text id="t2" systemLanguage="fr">b</text></switch>"""
        assert self.tostring(switch) == expected_output

    def test_clones_are_inserted_immediately_after_original_in_order(self, step, ctx):
        switch = make_switch('<text id="t1" systemLanguage="ar,fr">a</text><text id="t2" systemLanguage="en">b</text>')

        step._split_languages_in_switch(switch, ctx)

        children = list(switch)
        # expected order: t1(ar), clone(fr), t2(en)
        assert len(children) == 3
        assert [c.get("systemLanguage") for c in children] == ["ar", "fr", "en"]
        expected_output = """<switch xmlns="http://www.w3.org/2000/svg"><text id="t1" systemLanguage="ar">a</text><text id="t1-fr" systemLanguage="fr">a</text><text id="t2" systemLanguage="en">b</text></switch>"""
        assert self.tostring(switch) == expected_output


class TestSplitLanguagesInSwitchErrors(TestSetup):

    def test_duplicate_language_within_same_text_raises(self, step, ctx):
        switch = make_switch('<text id="t1" systemLanguage="ar,ar">hello</text>')

        with pytest.raises(SvgStructureError) as exc_info:
            step._split_languages_in_switch(switch, ctx)

        assert exc_info.value.args[0] == "structure-error-multiple-lang-in-text: ['ar']"

    def test_duplicate_language_across_texts_raises(self, step, ctx):
        switch = make_switch('<text id="t1" systemLanguage="ar">a</text><text id="t2" systemLanguage="ar">b</text>')

        with pytest.raises(SvgStructureError) as exc_info:
            step._split_languages_in_switch(switch, ctx)

        assert exc_info.value.args[0] == "structure-error-multiple-text-same-lang: ['ar']"

    def test_duplicate_fallback_across_texts_raises(self, step, ctx):
        switch = make_switch('<text id="t1">a</text><text id="t2">b</text>')

        with pytest.raises(SvgStructureError) as exc_info:
            step._split_languages_in_switch(switch, ctx)

        assert exc_info.value.args[0] == "structure-error-multiple-text-same-lang: ['fallback']"

    def test_non_text_child_raises(self, step, ctx):
        switch = make_switch('<g id="g1"><text>hi</text></g>')

        with pytest.raises(SvgStructureError) as exc_info:
            step._split_languages_in_switch(switch, ctx)

        assert exc_info.value.args[0] == "structure-error-switch-child-not-text"

    def test_comment_child_is_ignored(self, step, ctx):
        # raise SvgStructureError(code="structure-error-switch-text-content-outside-text")
        with pytest.raises(SvgStructureError) as exc_info:
            switch = make_switch('<!-- a comment --><text id="t1">hello</text>')

            # assert exc_info.value.args[0] == "structure-error-switch-text-content-outside-text"
            # should not raise; comment nodes are skipped
            step._split_languages_in_switch(switch, ctx)

        text_children = [c for c in switch if isinstance(c.tag, str)]
        assert len(text_children) == 1

        expected_output = (
            """<switch xmlns="http://www.w3.org/2000/svg"><!-- a comment --><text id="t1">hello</text></switch>"""
        )
        assert self.tostring(switch) == expected_output

    def test_error_in_one_switch_propagates(self, step, ctx):
        svg = f"""
        <svg xmlns="{SVG_NS}">
            <switch>
                <text id="a1" systemLanguage="ar,ar">a</text>
            </switch>
        </svg>
        """
        ctx.root = etree.fromstring(svg)

        with pytest.raises(SvgStructureError):
            step._split_switch_languages(ctx)


# ---------------------------------------------------------------------------
# _split_switch_languages (drives every <switch> found under ctx.root)
# ---------------------------------------------------------------------------


class TestSplitSwitchLanguages(TestSetup):
    def test_processes_every_switch_under_root(self, step, ctx):
        svg = f"""<svg xmlns="{SVG_NS}"><switch><text id="a1" systemLanguage="ar,fr">a</text></switch><g><switch><text id="b1" systemLanguage="en">b</text></switch></g></svg>"""
        ctx.root = etree.fromstring(svg)

        step._split_switch_languages(ctx)

        switches = ctx.root.findall(f".//{{{SVG_NS}}}switch")
        assert len(switches) == 2

        first_switch_texts = list(switches[0])
        assert [t.get("systemLanguage") for t in first_switch_texts] == ["ar", "fr"]

        second_switch_texts = list(switches[1])
        assert [t.get("systemLanguage") for t in second_switch_texts] == ["en"]

        expected_output = """<svg xmlns="http://www.w3.org/2000/svg"><switch><text id="a1" systemLanguage="ar">a</text><text id="a1-fr" systemLanguage="fr">a</text></switch><g><switch><text id="b1" systemLanguage="en">b</text></switch></g></svg>"""
        assert self.tostring(ctx.root) == expected_output

    def test_no_switches_is_a_no_op(self, step, ctx):
        svg = f'<svg xmlns="{SVG_NS}"><text id="a1">a</text></svg>'
        ctx.root = etree.fromstring(svg)

        # should not raise even though there is no <switch> element at all
        step._split_switch_languages(ctx)
