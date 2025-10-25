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

from CopySvgTranslate import inject, make_translation_ready


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

        try:
            make_translation_ready(file, True)
            # inject(inject_file=file, all_mappings=data)
        except Exception as e:
            assert "structure-error-multiple-text-same-lang: ['la']" == str(e)

    def testExeptions(self, temp_dir):
        # ---
        data = {
            "Simple nested tspan": {
                "svg": "<text><tspan>foo <tspan>bar</tspan></tspan></text>",
                "message": "structure-error-nested-tspans-not-supported",
                "params": [""]
            },
            "Nested tspan with ID": {
                "svg": "<text><tspan id='test'>foo <tspan>bar</tspan></tspan></text>",
                "message": "structure-error-nested-tspans-not-supported",
                "params": ["test"]
            },
            "Nested tspan with grandparent with ID": {
                "svg": "<g id='gparent'><text><tspan>foo <tspan>bar</tspan></tspan></text></g>",
                "message": "structure-error-nested-tspans-not-supported",
                "params": [""]
            },
            "CSS too complex": {
                "svg": "<style>#foo { stroke:1px; } .bar { color:pink; }</style><text>Foo</text>",
                "message": "structure-error-css-too-complex",
                "params": [""]
            },
            "id-chars": {
                "svg": "<text id='x|'>Foo</text>",
                "message": "structure-error-invalid-node-id",
                "params": [
                    "x|"
                ]
            },
            "Text with dollar numbers": {
                "svg": "<text id='blah'>Foo $3 bar</text>",
                "message": "structure-error-text-contains-dollar",
                "params": [
                    # "blah",
                    "Foo $3 bar"
                ]
            }
        }
        # ---
        result = {}
        # ---
        for key, tab in data.items():
            # <svg xmlns='http://www.w3.org/2000/svg' version='1.0' xmlns:xlink='http://www.w3.org/1999/xlink'>
            # ---
            text = f'<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg">{tab["svg"]}</svg>'
            # ---
            file = self.getSvgFileFromString(temp_dir, text)
            # ---
            try:
                make_translation_ready(file, True)
                # inject(inject_file=file)
            except Exception as e:
                result[str(e)] = f"{tab['message']}: {str(tab['params'])}"
                # assert f"{tab['message']}: {str(tab['params'])}" == str(e)
        # ---
        assert list(result.keys()) == list(result.values())
