"""
بقية الاختبارات:

I:/svgtranslate_php/svgtranslate_php/tests/Model/Svg/SvgFileTest.php

"""

import pytest

from CopySVGTranslation.exceptions import (
    SvgStructureError,
)
from CopySVGTranslation.injection import (
    inject_file_and_save,
)
from CopySVGTranslation.preparation import make_translation_ready


class Testinject:
    """Comprehensive tests for text utility functions."""

    def normalize(self, file_text):
        return "".join([x.strip() for x in file_text.splitlines()])

    def getsvgfilefromstring(self, temp_dir, text):

        file = temp_dir / "file.svg"
        file.write_text(text.strip(), encoding="utf-8")

        return file

    def test_inject(self, temp_dir):
        source_xml = """
            <?xml version="1.0"?>
            <svg xmlns="http://www.w3.org/2000/svg">
                <switch>
                    <text>lang none</text>
                </switch>
            </svg>
        """
        file = self.getsvgfilefromstring(temp_dir, source_xml)

        data = {"new": {"lang none": {"la": "lang la"}}}

        tree, root = make_translation_ready(file)

        # write to file
        tree.write(str(file), pretty_print=True, xml_declaration=True, encoding="utf-8")

        _result = inject_file_and_save(
            inject_file=file,
            save_path=file,
            all_mappings=data,
            pretty_print=False,
        )
        file_text = file.read_text(encoding="utf-8")

        _expected_old = """
            <?xml version='1.0' encoding='UTF-8'?>
            <svg xmlns="http://www.w3.org/2000/svg">
                <switch>
                    <text id="trsvg2-la" systemLanguage="la">
                        <tspan id="trsvg1-la">lang la</tspan>
                    </text>
                    <text id="trsvg2">
                        <tspan id="trsvg1">lang none</tspan>
                    </text>
                </switch>
            </svg>
        """

        expected = """
            <?xml version='1.0' encoding='UTF-8'?>
            <svg xmlns="http://www.w3.org/2000/svg">
                <switch>
                    <text id="trsvg1-la" systemLanguage="la">
                        <tspan id="trsvg2-la">lang la</tspan>
                    </text>
                    <text id="trsvg1">
                        <tspan id="trsvg2">lang none</tspan>
                    </text>
                </switch>
            </svg>
        """
        normalized_text = self.normalize(file_text)

        assert normalized_text == self.normalize(expected)

    def test_adds_text_to_switch(self, temp_dir):
        source_xml = """
            <?xml version="1.0"?>
            <svg xmlns="http://www.w3.org/2000/svg">
                <switch>
                    <text>lang none</text>
                    <text systemLanguage="la">lang la</text>
                </switch>
            </svg>
        """
        _expected_old = """
            <?xml version='1.0' encoding='UTF-8'?>
            <svg xmlns="http://www.w3.org/2000/svg">
                <switch>
                    <text id="trsvg4">
                        <tspan id="trsvg2">lang none</tspan>
                    </text>
                    <text systemLanguage="la" id="trsvg3">
                        <tspan id="trsvg1">lang la (new)</tspan>
                    </text>
                </switch>
            </svg>
        """
        expected = """
            <?xml version='1.0' encoding='UTF-8'?>
            <svg xmlns="http://www.w3.org/2000/svg">
                <switch>
                    <text systemLanguage="la" id="trsvg2">
                        <tspan id="trsvg4">lang la (new)</tspan>
                    </text>
                    <text id="trsvg1">
                        <tspan id="trsvg3">lang none</tspan>
                    </text>
                </switch>
            </svg>

        """
        file = self.getsvgfilefromstring(temp_dir, source_xml)

        data = {"new": {"lang none": {"la": "lang la (new)"}}}

        tree, root = make_translation_ready(file)

        # write to file
        tree.write(str(file), pretty_print=True, xml_declaration=True, encoding="utf-8")

        _result = inject_file_and_save(
            inject_file=file,
            save_path=file,
            all_mappings=data,
            overwrite=True,
            pretty_print=True,
        )

        file_text = file.read_text(encoding="utf-8")
        normalized_text = self.normalize(file_text)

        assert normalized_text == self.normalize(expected)

    def test_adds_text_to_switch_samelang(self, temp_dir):
        source_xml = """
            <?xml version="1.0"?>
            <svg xmlns="http://www.w3.org/2000/svg">
                <switch id="testswitch">
                    <text systemLanguage="la">lang la (1)</text>
                    <text systemLanguage="la">lang la (2)</text>
                    <text>lang none</text>
                </switch>
            </svg>
        """
        file = self.getsvgfilefromstring(temp_dir, source_xml)

        data = {"new": {"lang none": {"la": "lang la (new)"}}}

        with pytest.raises(SvgStructureError) as excinfo:
            make_translation_ready(file)

        assert str(excinfo.value) == "structure-error: structure-error-multiple-text-same-lang: ['la']"
