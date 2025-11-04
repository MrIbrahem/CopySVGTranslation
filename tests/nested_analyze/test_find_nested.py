"""Additional comprehensive pytest tests for CopySVGTranslation."""

import json
import shutil
import sys
import tempfile
from pathlib import Path
from lxml import etree
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from CopySVGTranslation.nested_analyze.find_nested import match_nested_tags, fix_nested_file


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test use."""
    d = Path(tempfile.mkdtemp())
    yield d
    shutil.rmtree(d)


class TestNestedFiles:
    """Comprehensive tests for text utility functions."""

    def getSvgFileFromString(self, temp_dir, text):

        file = temp_dir / "file.svg"
        file.write_text(text, encoding='utf-8')

        return file

    def test_match_nested_one_url(self, temp_dir):
        file = self.getSvgFileFromString(
            temp_dir, '''<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="850" height="729.1" viewBox="0 0 850 729.1">
                <g id="header" class="HeaderView">
                <text x="10" y="64.6" style="font-size: 12.375px; fill: rgb(133, 133, 133); line-height: 1.2;">
                <tspan x="10" y="64.6">
                <tspan style="font-weight: 700;">2.</tspan>
                <tspan style="font-weight: 700;">
                Age standardization</tspan> Age standardization is an adjustment that makes it possible to compare populations
                with different age structures, by </tspan>
                <tspan x="10" y="79.4">standardizing them to a common reference population.</tspan>
                <tspan x="10" y="94.3"> 📄 Read more: <a href="https://ourworldindata.org/age-standardization"
                target="_blank" rel="noopener" style="text-decoration: underline;">How does
                age standardization make health metrics comparable?
                </a>
                </tspan>
                </text>
                </g>
            </svg>
        ''')
        len_result_before = len(match_nested_tags(file))
        _fix_file = fix_nested_file(file)
        len_result_after = len(match_nested_tags(file))

        assert len_result_before == 2
        assert len_result_after == 0

    def test_match_nested_multi_urls(self, temp_dir):
        file = self.getSvgFileFromString(
            temp_dir, '''<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="300" height="100"
            style="font-family: Lato, &quot;Helvetica Neue&quot;, Helvetica, Arial, &quot;Liberation Sans&quot;, sans-serif; font-feature-settings: &quot;liga&quot;, &quot;kern&quot;, &quot;calt&quot;,
            &quot;lnum&quot;; text-rendering: geometricprecision; -webkit-font-smoothing: antialiased; font-size: 18px;
            background-color: rgb(255, 255, 255);">
            <g id="header" class="HeaderView">
            <text id="origin-url" font-size="13.00" x="50" y="40.25">
            <tspan><a target="_blank" style="fill: #858585;"
            href="https://ourworldindata.org/obesity">OurWorldinData.org/obesity</a> | <a target="_blank"
            style="fill: #858585;" href="https://creativecommons.org/licenses/by/4.0/">CC BY</a></tspan>
            </text>
            </g>
        </svg>''')
        len_result_before = len(match_nested_tags(file))
        _fix_file = fix_nested_file(file)
        len_result_after = len(match_nested_tags(file))

        assert len_result_before == 1
        assert len_result_after == 0

    def test_match_nested_multi_tags(self, temp_dir):
        file = self.getSvgFileFromString(
            temp_dir, '''<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="850" height="729.1" viewBox="0 0 850 729.1"
                style="font-family: Lato, &quot;Helvetica Neue&quot;, Helvetica, Arial, &quot;Liberation Sans&quot;, sans-serif; text-rendering: geometricprecision; -webkit-font-smoothing: antialiased; font-size: 18px; background-color: rgb(255, 255, 255);">
                <g id="header" class="HeaderView">
                <g class="markdown-text-wrap">
                <text style="font-size: 12.375px; fill: rgb(133, 133, 133); line-height: 1.2;" x="0.0" y="64.6">
                <tspan x="0" y="64.6"> 2. Age
                standardization Age standardization is an adjustment that makes it
                possible to compare populations with different age structures, by </tspan>
                <tspan x="0" y="79.4">standardizing them to a common reference population.</tspan>
                <tspan x="0" y="94.3"> 📄 Read more: <a href="https://ourworldindata.org/age-standardization"
                target="_blank" rel="noopener" style="text-decoration: underline;">
                How does
                age standardization
                make health metrics comparable?</a></tspan></text></g></g></svg>'''
        )
        len_result_before = len(match_nested_tags(file))
        _fix_file = fix_nested_file(file)
        len_result_after = len(match_nested_tags(file))

        assert len_result_before == 1
        assert len_result_after == 0

    def test_match_nested_multi_tags2(self, temp_dir):
        file = self.getSvgFileFromString(
            temp_dir, '''<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="850" height="721.1"
                viewBox="0 0 850 721.1"
                style="font-family: Lato, &quot;Helvetica Neue&quot;, Helvetica, Arial, &quot;Liberation Sans&quot;, sans-serif; text-rendering: geometricprecision; -webkit-font-smoothing: antialiased; font-size: 18px; background-color: rgb(255, 255, 255);">
                <g class="markdown-text-wrap" id="subtitle">
                    <text fill="#5b5b5b" style="font-size: 15px; line-height: 1.2;" x="16.0" y="66.5">
                        <tspan xmlns="http://www.w3.org/2000/svg" x="16" y="66.5">Estimated annual number of
                            deaths attributed to <tspan class="dod-span" data-id="obesity">obesity<tspan
                                    style="font-feature-settings: &quot;sups&quot;;">¹</tspan></tspan> per
                            100,000 people.</tspan>
                    </text>
                </g>
            </svg>''')
        len_result_before = len(match_nested_tags(file))
        _fix_file = fix_nested_file(file)
        len_result_after = len(match_nested_tags(file))

        assert len_result_before == 2
        assert len_result_after == 0

    def test_match_nested_multi_tags_9(self, temp_dir):
        file = self.getSvgFileFromString(
            temp_dir, '''<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="850" height="758.8" viewBox="0 0 850 758.8"
                style="font-family: Lato, &quot;Helvetica Neue&quot;, Helvetica, Arial, &quot;Liberation Sans&quot;, sans-serif; font-feature-settings: &quot;liga&quot;, &quot;kern&quot;, &quot;calt&quot;, &quot;lnum&quot;; text-rendering: geometricprecision; -webkit-font-smoothing: antialiased; font-size: 18px; background-color: rgb(255, 255, 255);">
                <g id="footer" class="SourcesFooter" style="fill: rgb(133, 133, 133);">
                    <g id="sources" class="markdown-text-wrap"><text x="16.0" y="545.3" style="font-size: 13px; line-height: 1.2;">
                            <tspan x="16" y="545.3">
                                <tspan style="font-weight: 700;">Data source:</tspan> IHME, Global Burden of Disease (2024)
                            </tspan>
                        </text></g>
                    <g id="note" class="markdown-text-wrap"><text x="16.0" y="565.4" style="font-size: 13px; line-height: 1.2;">
                            <tspan x="16" y="565.4">
                                <tspan style="font-weight: 700;">Note:</tspan> To allow for comparisons between countries and over
                                time, this metric is <tspan class="dod-span" data-id="age_standardized">age-standardized<tspan
                                        style="font-feature-settings: &quot;sups&quot;;">²</tspan>
                                </tspan>. Obesity is defined as having a body-mass
                            </tspan>
                            <tspan x="16" y="581.0">index (BMI) ≥ 30. BMI is a person's weight (in kilograms) divided by their
                                height (in meters) squared.</tspan>
                        </text></g><text id="origin-url" font-size="13.00" x="622.8" y="545.3">
                        <tspan x="622.75" y="545.3100000000001"><a target="_blank" style="fill: #858585;"
                                href="https://ourworldindata.org/obesity">OurWorldinData.org/obesity</a> | <a target="_blank"
                                style="fill: #858585;" href="https://creativecommons.org/licenses/by/4.0/">CC BY</a></tspan>
                    </text>
                </g>
                <line id="separator-line" x1="16" y1="600" x2="834" y2="600" stroke="#e7e7e7" />
                <g id="details" transform="translate(15, 616)">
                    <g class="markdown-text-wrap"><text x="0.0" y="12.0"
                            style="font-size: 12.375px; fill: rgb(133, 133, 133); line-height: 1.2;">
                            <tspan x="0" y="12.0">
                                <tspan style="font-weight: 700;">1.</tspan>
                                <tspan style="font-weight: 700;">Obesity</tspan> Obesity is defined as having a body-mass index
                                (BMI) above 30.
                            </tspan>
                            <tspan x="0" y="26.9">A person’s BMI is calculated as their weight (in kilograms) divided by their
                                height (in meters) squared. For example, someone measuring 1.60</tspan>
                            <tspan x="0" y="41.7">meters and weighing 64 kilograms has a BMI of 64 / 1.6² = 25.</tspan>
                            <tspan x="0" y="56.6">Obesity increases the mortality risk of many conditions, including cardiovascular
                                disease, gastrointestinal disorders, type 2 diabetes, joint and</tspan>
                            <tspan x="0" y="71.4">muscular disorders, respiratory problems, and psychological issues.</tspan>
                        </text></g>
                    <g class="markdown-text-wrap"><text x="0.0" y="94.3"
                            style="font-size: 12.375px; fill: rgb(133, 133, 133); line-height: 1.2;">
                            <tspan x="0" y="94.3">
                                <tspan style="font-weight: 700;">2.</tspan>
                                <tspan style="font-weight: 700;">Age standardization</tspan> Age standardization is an adjustment
                                that makes it possible to compare populations with different age structures, by
                            </tspan>
                            <tspan x="0" y="109.1">standardizing them to a common reference population.</tspan>
                            <tspan x="0" y="124.0">📄 Read more: <a href="https://ourworldindata.org/age-standardization"
                                    target="_blank" rel="noopener" style="text-decoration: underline;">How does age standardization
                                    make health metrics comparable?</a></tspan>
                        </text></g>
                </g>
            </svg>''')
        len_result_before = len(match_nested_tags(file))
        _fix_file = fix_nested_file(file)
        len_result_after = len(match_nested_tags(file))

        assert len_result_before == 7
        assert len_result_after == 0
