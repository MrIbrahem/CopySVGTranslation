"""
بقية الاختبارات:

I:/svgtranslate_php/svgtranslate_php/tests/Model/Svg/SvgFileTest.php

"""

from pathlib import Path

import pytest
from lxml import etree

from CopySVGTranslation import TranslationConfig
from CopySVGTranslation.exceptions import (
    SvgStructureError,
)
from CopySVGTranslation.legacy.inject import inject_file_tree
from CopySVGTranslation.preparation import SvgPreparationPipeline


def preparer_run(source_file: Path | str) -> tuple[etree._ElementTree, etree._Element]:
    """
    Legacy function-style wrapper around SvgPreparationPipeline, kept for
    backward compatibility with existing callers.
    """
    config = TranslationConfig(
        nested_strategy="raise",
    )
    preparer = SvgPreparationPipeline(config)
    return preparer.run(path=source_file)


class Testinject:
    """Comprehensive tests for text utility functions."""

    def normalize(self, file_text):
        return "".join([x.strip() for x in file_text.splitlines()])

    def getsvgfilefromstring(self, temp_dir, text):

        file = temp_dir / "file.svg"
        file.write_text(text.strip(), encoding="utf-8")

        return file

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
                    <text systemLanguage="la" id="trsvg3">
                        <tspan id="trsvg1">lang la (new)</tspan>
                    </text>
                    <text id="trsvg4">
                        <tspan id="trsvg2">lang none</tspan>
                    </text>
                </switch>
            </svg>
        """
        expected = """
            <?xml version='1.0' encoding='UTF-8'?>
            <svg xmlns="http://www.w3.org/2000/svg">
                <switch>
                    <text id="trsvg1">
                        <tspan id="trsvg2">lang none</tspan>
                    </text>
                    <text systemLanguage="la" id="trsvg3">
                        <tspan id="trsvg4">lang la (new)</tspan>
                    </text>
                </switch>
            </svg>

        """
        file = self.getsvgfilefromstring(temp_dir, source_xml)

        data = {"new": {"lang none": {"la": "lang la (new)"}}}

        tree, root = preparer_run(file)

        # write to file
        tree.write(str(file), pretty_print=True, xml_declaration=True, encoding="utf-8")

        _result = inject_file_tree(
            inject_file=file,
            save_path=file,
            mapping=data,
            overwrite_translations=True,
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
            preparer_run(file)

        assert str(excinfo.value) == "structure-error-multiple-text-same-lang: ['la']"

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

        tree, root = preparer_run(file)

        # write to file
        tree.write(str(file), pretty_print=True, xml_declaration=True, encoding="utf-8")

        _result = inject_file_tree(
            inject_file=file,
            save_path=file,
            mapping=data,
            pretty_print=False,
            sort_switches=True,
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

        assert '<text id="trsvg1"><tspan id="trsvg2">lang none</tspan></text>' in normalized_text
        assert (
            '<text id="trsvg1-la" systemLanguage="la"><tspan id="trsvg2-la">lang la</tspan></text>' in normalized_text
        )

        assert normalized_text == self.normalize(expected)
