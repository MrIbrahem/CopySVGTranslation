"""
بقية الاختبارات:

I:/svgtranslate_php/svgtranslate_php/tests/Model/Svg/SvgFileTest.php

"""

import sys
import pytest
import shutil
import tempfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from CopySVGTranslation import inject, make_translation_ready, start_injects
from CopySVGTranslation.injection import (
    SvgNestedTspanException,
    SvgStructureException,
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test use."""
    d = Path(tempfile.mkdtemp())
    yield d
    shutil.rmtree(d)


class Testinject:
    """Comprehensive tests for text utility functions."""

    def getSvgFileFromString(self, temp_dir, text):

        file = temp_dir / "file.svg"
        file.write_text(text, encoding='utf-8')

        return file

    def test_inject(self, temp_dir):
        file = self.getSvgFileFromString(
            temp_dir,
            '<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><switch><text>lang none</text></switch></svg>'
        )

        data = {"new": {"lang none": {"la": "lang la"}}}

        make_translation_ready(file, True)

        _result = inject(inject_file=file, all_mappings=data, save_result=True, pretty_print=False)
        file_text = file.read_text(encoding="utf-8")
        expected = """<?xml version='1.0' encoding='UTF-8'?>\n<svg xmlns="http://www.w3.org/2000/svg"><switch><text id="trsvg2-la" systemLanguage="la"><tspan id="trsvg1-la">lang la</tspan></text><text id="trsvg2"><tspan id="trsvg1">lang none</tspan></text></switch></svg>"""
        assert file_text == expected

    def testAddsTextToSwitch(self, temp_dir):
        file = self.getSvgFileFromString(
            temp_dir,
            '''<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><switch><text systemLanguage="la">lang la</text><text>lang none</text></switch></svg>'''
        )

        data = {"new": {"lang none": {"la": "lang la (new)"}}}

        make_translation_ready(file, True)

        _result = inject(inject_file=file, all_mappings=data, save_result=True, overwrite=True, pretty_print=False)
        file_text = file.read_text(encoding="utf-8")
        expected = """<?xml version='1.0' encoding='UTF-8'?>\n<svg xmlns="http://www.w3.org/2000/svg"><switch><text systemLanguage="la" id="trsvg3"><tspan id="trsvg1">lang la (new)</tspan></text><text id="trsvg4"><tspan id="trsvg2">lang none</tspan></text></switch></svg>"""
        assert file_text == expected

    def testAddsTextToSwitchSameLang(self, temp_dir):
        file = self.getSvgFileFromString(
            temp_dir,
            '''<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><switch id="testswitch"><text systemLanguage="la">lang la (1)</text><text systemLanguage="la">lang la (2)</text><text>lang none</text></switch></svg>'''
        )

        data = {"new": {"lang none": {"la": "lang la (new)"}}}

        with pytest.raises(SvgStructureException) as excinfo:
            make_translation_ready(file, True)
        assert str(excinfo.value) == "structure-error-multiple-text-same-lang: ['la']"

    @pytest.mark.parametrize(
        "svg, exc_type, code, extra",
        [
            ("<text><tspan>foo <tspan>bar</tspan></tspan></text>", SvgNestedTspanException, "structure-error-nested-tspans-not-supported", [""]),
            ("<text><tspan id='test'>foo <tspan>bar</tspan></tspan></text>", SvgNestedTspanException, "structure-error-nested-tspans-not-supported", ["test"]),
            ("<g id='gparent'><text><tspan>foo <tspan>bar</tspan></tspan></text></g>", SvgNestedTspanException, "structure-error-nested-tspans-not-supported", [""]),
            ("<style>#foo { stroke:1px; } .bar { color:pink; }</style><text>Foo</text>", SvgStructureException, "structure-error-css-too-complex", [""]),
            ("<text id='x|'>Foo</text>", SvgStructureException, "structure-error-invalid-node-id", ["x|"]),
            ("<text id='blah'>Foo $3 bar</text>", SvgStructureException, "structure-error-text-contains-dollar", ["Foo $3 bar"]),
        ],
    )
    def testExeptions(self, temp_dir, svg, exc_type, code, extra):
        text = f'<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg">{svg}</svg>'
        file = self.getSvgFileFromString(temp_dir, text)

        with pytest.raises(exc_type) as excinfo:
            make_translation_ready(file, True)

        assert excinfo.value.code == code
        assert excinfo.value.extra == extra

    def test_start_injects_counts_nested_tspans(self, temp_dir):
        nested_svg = "<?xml version=\"1.0\"?><svg xmlns=\"http://www.w3.org/2000/svg\"><text><tspan>foo <tspan>bar</tspan></tspan></text></svg>"
        file = self.getSvgFileFromString(temp_dir, nested_svg)

        result = start_injects(
            [str(file)],
            translations={"new": {"dummy": {"la": "value"}}},
            output_dir_translated=temp_dir,
        )

        assert result["nested_files"] == 1
        assert file.name in result["nested_files_list"]
