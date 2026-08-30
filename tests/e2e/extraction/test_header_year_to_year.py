""" """

from pathlib import Path

import pytest

from CopySVGTranslation.config import TranslationConfig
from CopySVGTranslation.core.mapping import TranslationMapping
from CopySVGTranslation.extraction.extractor import SVGTranslationExtractor
from CopySVGTranslation.io.svg_document import SvgDocument
from CopySVGTranslation.titles.year_to_year_handler import YearTitleHandlerNew


def _wrap_svg(inner: str) -> str:
    return f"""\
    <svg xmlns="http://www.w3.org/2000/svg">
        <g class="HeaderView" id="header">
            <a href="https://ourworldindata.org/grapher/wine-production?tab=line&amp;country=~ALB&amp;overlay=download-vis"
            id="title"
            style="font-family: &quot;Playfair Display&quot;, Georgia, &quot;Times New Roman&quot;, &quot;Liberation Serif&quot;, serif;">
            {inner}
            </a>
        </g>
    </svg>
"""


def _write_svg(temp_dir: Path, inner_svg: str, name: str = "test.svg"):
    """Write *inner_svg* to a temporary SVG file and return its Path."""
    svg_file = temp_dir / name
    svg_file.write_text(_wrap_svg(inner_svg), encoding="utf-8")
    return svg_file


WINE_PRODUCTION_ALB_HEADER = """
    <switch>
        <text fill="#2d2e2d" font-size="25.00" font-weight="600" x="16.0" y="40.3" id="trsvg1">
        <tspan x="16" y="40.25" id="trsvg2">Wine production, 1961 to 2023</tspan>
        </text>
    </switch>
"""

WINE_PRODUCTION_ALB_JSON = {
    "error": "",
    "meta": {"header": {"wine production, 1961 to 2023": {}}},
    "new": {"wine production, 1961 to 2023": {}},
    "title_new": {},
    "tspans_by_id": {"trsvg2": "Wine production, 1961 to 2023"},
}

WINE_PRODUCTION_WORLD_1961_HEADER = """
    <switch>
        <text fill="#2d2e2d" font-size="25.00" font-weight="normal" x="16.0" y="40.3" id="trsvg13-af" systemLanguage="af">
            <tspan x="16" y="40.25" id="trsvg1-af">Wynproduksie, 1961</tspan>
        </text>
        <text fill="#2d2e2d" font-size="25.00" font-weight="normal" x="16.0" y="40.3" id="trsvg13-ar" systemLanguage="ar">
            <tspan x="16" y="40.25" id="trsvg1-ar">إنتاج النبيذ، 1961</tspan>
        </text>
        <text fill="#2d2e2d" font-size="25.00" font-weight="600" x="16.0" y="40.3" id="trsvg13">
            <tspan x="16" y="40.25" id="trsvg1">Wine production, 1961</tspan>
        </text>
    </switch>
"""

WINE_PRODUCTION_WORLD_1961_JSON = {
    "new": {
        "wine production, 1961": {"af": "Wynproduksie, 1961", "ar": "إنتاج النبيذ، 1961"},
    },
    "title_new": {"wine production, {year}": {"af": "Wynproduksie, {year}", "ar": "إنتاج النبيذ، {year}"}},
    "tspans_by_id": {"trsvg1": "Wine production, 1961"},
    "meta": {"header": {"wine production, 1961": {"af": "Wynproduksie, 1961", "ar": "إنتاج النبيذ، 1961"}}},
    "error": "",
}

TEXT_NO_LANGS = """
    <switch>
        <text fill="#2d2e2d" font-size="25.00" font-weight="600" x="16.0" y="40.3" id="trsvg13">
            <tspan x="16" y="40.25" id="trsvg1">Wine production, 1961</tspan>
        </text>
    </switch>
"""


class TestSetup:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.service = SVGTranslationExtractor(TranslationConfig(set_key_with_empty_value=False))


def test_extract_no_langs(temp_dir):

    service = SVGTranslationExtractor(TranslationConfig(set_key_with_empty_value=False))

    svg_file = _write_svg(temp_dir, TEXT_NO_LANGS, name="test2.svg")
    _result = service.extract(svg_file)
    result = _result.to_json()

    assert result["title_new"] == {}


class TestWineProductionAlb(TestSetup):

    def test_wine_production_alb(self, temp_dir):
        svg_file = _write_svg(temp_dir, WINE_PRODUCTION_ALB_HEADER)
        _result = self.service.extract(svg_file)
        result = _result.to_json()

        assert result == WINE_PRODUCTION_ALB_JSON

        doc = SvgDocument.load(svg_file)
        _result1 = self.service.extract_from_root(doc.root)

        assert _result1 == _result

    def test_build_title_new_templates(self):
        result = self.service.year_handler.build_title_new_templates(
            WINE_PRODUCTION_ALB_JSON["new"],
            set_key_with_empty_value=False,
        )
        assert result == {}


class TestWineProductionWorld1961(TestSetup):

    def test_wine_production_world_1961(self, temp_dir):
        svg_file = _write_svg(temp_dir, WINE_PRODUCTION_WORLD_1961_HEADER)

        _result = self.service.extract(svg_file)
        result = _result.to_json()

        assert result == WINE_PRODUCTION_WORLD_1961_JSON

    def test_build_title_new_templates(self):
        result = self.service.year_handler.build_title_new_templates(
            WINE_PRODUCTION_WORLD_1961_JSON["new"],
            set_key_with_empty_value=False,
        )
        assert result == {"wine production, {year}": {"af": "Wynproduksie, {year}", "ar": "إنتاج النبيذ، {year}"}}


class TestExamples(TestSetup):

    def test_build_title_new_templates(self):
        new = {
            "test, 2012": {},
            "wine production, 1961": {"af": "Wynproduksie, 1961", "ar": "إنتاج النبيذ، 1961"},
            "wine production, 1961 to 2023": {},
        }
        result = self.service.year_handler.build_title_new_templates(
            new,
            create_lang_template=True,
            set_key_with_empty_value=False,
        )

        assert "test, {year}" not in result
        assert result["wine production, {year}"] == {"af": "Wynproduksie, {year}", "ar": "إنتاج النبيذ، {year}"}

    def test_set_key_with_empty_value(self):
        new = {
            "test, 2012": {},
            "wine production, 1961": {"af": "Wynproduksie, 1961", "ar": "إنتاج النبيذ، 1961"},
            "wine production, 1961 to 2023": {},
        }
        result = self.service.year_handler.build_title_new_templates(
            new,
            create_lang_template=True,
            set_key_with_empty_value=True,
        )
        assert "test, {year}" in result
        assert result["test, {year}"] == {}


class TestWhatTODODone:
    @pytest.fixture(autouse=True)
    def setup(self):
        new = {
            "test, 2012": {},
            "wine production, 1961": {"af": "Wynproduksie, 1961", "ar": "إنتاج النبيذ، 1961"},
            "wine production, 1961 to 2023": {"ar": "إنتاج النبيذ، 1961 إلى 2023"},
        }
        self.service = YearTitleHandlerNew()
        self.mapping = TranslationMapping(new=new)
        self.result = self.service.build_title_new_templates_year1_to_year2(
            self.mapping,
            set_key_with_empty_value=True,
        )

    def test_match_years(self):
        year1, year2 = self.service.match_years("wine production, 1961 to 2023")
        assert year1 == "1961"
        assert year2 == "2023"

    def test_set_year1_to_year2_done(self):
        assert "wine production, {year1} to {year2}" in self.result
        assert self.result["wine production, {year1} to {year2}"] == {"ar": "إنتاج النبيذ، {year1} إلى {year2}"}

    def test_extend_translations_diff(self):
        title_new = {"ar": "إنتاج النبيذ، {year}"}
        result = self.service.extend_translations(title_new)

        assert result == {"ar": "إنتاج النبيذ، {year1} إلى {year2}"}


class TestWhatTODO:

    @pytest.fixture(autouse=True)
    def setup_todo(self):
        self.service = YearTitleHandlerNew(TranslationConfig(set_key_with_empty_value=True, enable_year_titles=True))

    @pytest.mark.todo
    def test_translation_mapping_years(self):
        new = {
            "wine production, 1961 to 2023": {},
        }
        title_new = {
            "wine production, {year}": {"ar": "إنتاج النبيذ، {year}"}
        }
        mapping = TranslationMapping(title_new=title_new, new=new)

        data = self.service.build_title_new_templates_year1_to_year2(mapping)

        assert "wine production, {year1} to {year2}" in data
        assert data["wine production, {year1} to {year2}"] == {"ar": "إنتاج النبيذ، {year1} إلى {year2}"}

    @pytest.mark.todo
    def test_set_year1_to_year2(self):
        new = {
            "wine production, 1961 to 2023": {},
        }
        title_new = {
            "wine production, {year}": {"ar": "إنتاج النبيذ، {year}"}
        }
        mapping = TranslationMapping(title_new=title_new, new=new)

        self.service.build_templates(mapping)
        assert "wine production, {year1} to {year2}" in mapping.title_new
        assert mapping.new == { "wine production, 1961 to 2023": {}}, "new diff"

        assert mapping.title_new["wine production, {year1} to {year2}"] == {"ar": "إنتاج النبيذ، {year1} إلى {year2}"}, "title_new diff"
