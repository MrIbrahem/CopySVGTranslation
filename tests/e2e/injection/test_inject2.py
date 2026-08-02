"""
بقية الاختبارات:

I:/svgtranslate_php/svgtranslate_php/tests/Model/Svg/SvgFileTest.php

"""

import pytest

from CopySVGTranslation.injection import (
    inject,
    make_translation_ready,
)
from CopySVGTranslation.injection.exceptions import (
    SvgNestedTspanExceptionError,
    SvgStructureExceptionError,
)


class Testinject:
    """Comprehensive tests for text utility functions."""

    def getsvgfilefromstring(self, temp_dir, text):

        file = temp_dir / "file.svg"
        file.write_text(text, encoding="utf-8")

        return file

    def test_inject(self, temp_dir):
        file = self.getsvgfilefromstring(
            temp_dir,
            '<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><switch><text>lang none</text></switch></svg>',
        )

        data = {"new": {"lang none": {"la": "lang la"}}}

        tree, root = make_translation_ready(file)

        # write to file
        tree.write(str(file), pretty_print=True, xml_declaration=True, encoding="utf-8")

        _result = inject(
            inject_file=file,
            all_mappings=data,
            save_result=True,
            pretty_print=False,
        )
        file_text = file.read_text(encoding="utf-8")
        expected = """<?xml version='1.0' encoding='UTF-8'?>\n<svg xmlns="http://www.w3.org/2000/svg"><switch><text id="trsvg2-la" systemLanguage="la"><tspan id="trsvg1-la">lang la</tspan></text><text id="trsvg2"><tspan id="trsvg1">lang none</tspan></text></switch></svg>"""
        assert file_text == expected

    def testaddstexttoswitch(self, temp_dir):
        file = self.getsvgfilefromstring(
            temp_dir,
            """<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><switch><text systemLanguage="la">lang la</text><text>lang none</text></switch></svg>""",
        )

        data = {"new": {"lang none": {"la": "lang la (new)"}}}

        tree, root = make_translation_ready(file)

        # write to file
        tree.write(str(file), pretty_print=True, xml_declaration=True, encoding="utf-8")

        _result = inject(
            inject_file=file,
            all_mappings=data,
            save_result=True,
            overwrite=True,
            pretty_print=False,
        )
        file_text = file.read_text(encoding="utf-8")
        expected = """<?xml version='1.0' encoding='UTF-8'?>\n<svg xmlns="http://www.w3.org/2000/svg"><switch><text systemLanguage="la" id="trsvg3"><tspan id="trsvg1">lang la (new)</tspan></text><text id="trsvg4"><tspan id="trsvg2">lang none</tspan></text></switch></svg>"""
        assert file_text == expected

    def testaddstexttoswitchsamelang(self, temp_dir):
        file = self.getsvgfilefromstring(
            temp_dir,
            """<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><switch id="testswitch"><text systemLanguage="la">lang la (1)</text><text systemLanguage="la">lang la (2)</text><text>lang none</text></switch></svg>""",
        )

        data = {"new": {"lang none": {"la": "lang la (new)"}}}

        with pytest.raises(SvgStructureExceptionError) as excinfo:
            make_translation_ready(file)
        assert str(excinfo.value) == "structure-error-multiple-text-same-lang: ['la']"

    @pytest.mark.parametrize(
        "svg, exc_type, code, extra",
        [
            (
                "<text><tspan>foo <tspan>bar</tspan></tspan></text>",
                SvgNestedTspanExceptionError,
                "structure-error-nested-tspans-not-supported",
                [""],
            ),
            (
                "<text><tspan id='test'>foo <tspan>bar</tspan></tspan></text>",
                SvgNestedTspanExceptionError,
                "structure-error-nested-tspans-not-supported",
                ["test"],
            ),
            (
                "<g id='gparent'><text><tspan>foo <tspan>bar</tspan></tspan></text></g>",
                SvgNestedTspanExceptionError,
                "structure-error-nested-tspans-not-supported",
                [""],
            ),
            (
                "<style>#foo { stroke:1px; } .bar { color:pink; }</style><text>Foo</text>",
                SvgStructureExceptionError,
                "structure-error-css-too-complex",
                [""],
            ),
            ("<text id='x|'>Foo</text>", SvgStructureExceptionError, "structure-error-invalid-node-id", ["x|"]),
            (
                "<text id='blah'>Foo $3 bar</text>",
                SvgStructureExceptionError,
                "structure-error-text-contains-dollar",
                ["Foo $3 bar"],
            ),
        ],
    )
    def test_exeptions(self, temp_dir, svg, exc_type, code, extra):
        text = f'<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg">{svg}</svg>'
        file = self.getsvgfilefromstring(temp_dir, text)

        with pytest.raises(exc_type) as excinfo:
            make_translation_ready(file)

        assert excinfo.value.code == code
        assert excinfo.value.extra == extra
