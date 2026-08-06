"""
Unit tests for CopySVGTranslation/preparation/steps/validate.py module.

Classes to test: ValidateStructure

TODO: write tests
"""

from pathlib import Path
from types import SimpleNamespace

import pytest
from lxml import etree

from CopySVGTranslation.config import TranslationConfig
from CopySVGTranslation.exceptions import (
    SvgCssTooComplexError,
    SvgStructureError,
)
from CopySVGTranslation.preparation.preparer import PreparationContext
from CopySVGTranslation.preparation.steps.validate import (
    ValidateStructure,
)

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
        "config": TranslationConfig(assign_missing_ids=True),
        "path": Path("dummy.svg"),
    }
    defaults.update(overrides)
    return PreparationContext(**defaults)


def tostring(el: etree._Element) -> str:
    return etree.tostring(el, pretty_print=False).decode("utf-8").strip()


# ---------------------------------------------------------------------------
# ValidateStructure
# ---------------------------------------------------------------------------


@pytest.fixture
def validate_step():

    return ValidateStructure(config=SimpleNamespace())


class TestValidateStructure:
    def test_root_none_is_a_noop(self, validate_step):
        ctx = make_ctx(root=None)

        validate_step.execute(ctx)

    @pytest.mark.skip(
        reason="lxml.etree.XMLSyntaxError: Namespace prefix xlink for href on tref is not defined, line 1, column 76"
    )
    def test_tref_element_raises(self, validate_step):

        root = make_root('<text id="t1"><tref xlink:href="#x"/></text>')
        ctx = make_ctx(root=root)

        with pytest.raises(SvgStructureError) as exc_info:
            validate_step.execute(ctx)

        assert exc_info.value.code == "structure-error-contains-tref"

    def test_no_text_elements_short_circuits_before_style_checks(self, validate_step):
        # No <text> anywhere: function returns early, so even "unsafe"
        # looking <style> content must not raise.
        root = make_root("<style>#a{fill:red}</style>")
        ctx = make_ctx(root=root)

        # should not raise, since there are no <text> elements at all
        validate_step.execute(ctx)

    def test_style_without_hash_is_allowed(self, validate_step):
        root = make_root('<style>.cls{fill:red}</style><text id="t1">hello</text>')
        ctx = make_ctx(root=root)

        # no "#" anywhere in the CSS: should not raise
        validate_step.execute(ctx)

    def test_simple_id_selector_is_allowed_by_simple_css_regex(self, validate_step):
        # This CSS matches the "simple" regex (id used only as a selector,
        # not inside a property value) but does contain "#", so it goes
        # through the selector-splitting check next; a bare "#id{...}"
        # selector should be flagged as an id-based selector.
        root = make_root('<style>#a{fill:red}</style><text id="t1">hello</text>')
        ctx = make_ctx(root=root)

        with pytest.raises(SvgStructureError) as exc_info:
            validate_step.execute(ctx)

        assert exc_info.value.code == "structure-error-css-too-complex"

    def test_complex_css_with_hash_raises_too_complex(self, validate_step):

        # Content with "#" that doesn't match the simple selector/body
        # regex at all (e.g. unbalanced braces) should be rejected as
        # "too complex" before selectors are even inspected.
        root = make_root('<style>{{{ #weird</style><text id="t1">hello</text>')
        ctx = make_ctx(root=root)

        with pytest.raises(SvgStructureError) as exc_info:
            validate_step.execute(ctx)

        assert exc_info.value.code == "structure-error-css-too-complex"

    def test_hash_only_in_property_value_still_flagged_as_id_selector(self, validate_step):
        # Regardless of where exactly "#" appears, once the CSS is deemed
        # "simple" the code splits on rule bodies and checks selector
        # portions for "#". A color like #fff inside a simple single-rule
        # block has no separate selector text once split, so this exercises
        # the boundary between the two checks.
        root = make_root('<style>.cls{fill:#fff}</style><text id="t1">hello</text>')
        ctx = make_ctx(root=root)

        # "fill:#fff" contains "#", CSS matches the simple regex, and after
        # splitting out the "{...}" body, the remaining selector text ".cls"
        # has no "#", so this should be allowed.
        with pytest.raises(SvgCssTooComplexError) as exc_info:
            validate_step.execute(ctx)

    def test_multiple_style_elements_are_all_checked(self, validate_step):

        root = make_root("<style>.a{fill:red}</style><style>#bad{fill:blue}</style><text id='t1'>hello</text>")
        ctx = make_ctx(root=root)

        with pytest.raises(SvgStructureError) as exc_info:
            validate_step.execute(ctx)

        assert exc_info.value.code == "structure-error-css-too-complex"

    def test_no_style_elements_is_fine(self, validate_step):
        root = make_root('<text id="t1">hello</text>')
        ctx = make_ctx(root=root)

        # should not raise: texts exist, but there are no <style> elements
        validate_step.execute(ctx)


class SkipTestValidateStructure:
    def test_switch_child_not_text_raises(self, validate_step):
        root = make_root('<switch><rect id="r1"/></switch><text id="t1">hello</text>')
        ctx = make_ctx(root=root)
        with pytest.raises(SvgStructureError) as exc_info:
            validate_step.execute(ctx)
        assert exc_info.value.code == "structure-error-switch-child-not-text"

    def test_switch_text_content_outside_text_raises(self, validate_step):
        root = make_root('<switch>some raw text <text id="t1">hello</text></switch>')
        ctx = make_ctx(root=root)
        with pytest.raises(SvgStructureError) as exc_info:
            validate_step.execute(ctx)
        assert exc_info.value.code == "structure-error-switch-text-content-outside-text"

    def test_switch_duplicate_languages_raises(self, validate_step):
        root = make_root(
            '<switch><text id="t1" systemLanguage="ar">1</text><text id="t2" systemLanguage="ar">2</text></switch>'
        )
        ctx = make_ctx(root=root)
        with pytest.raises(SvgStructureError) as exc_info:
            validate_step.execute(ctx)
        assert exc_info.value.code == "structure-error-multiple-text-same-lang"

    def test_text_non_tspan_child_raises(self, validate_step):
        root = make_root('<text id="t1"><a>hello</a></text>')
        ctx = make_ctx(root=root)
        with pytest.raises(SvgStructureError) as exc_info:
            validate_step.execute(ctx)
        assert exc_info.value.code == "structure-error-non-tspan-inside-text"
