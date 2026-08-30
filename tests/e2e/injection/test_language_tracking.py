import textwrap
from pathlib import Path

from CopySVGTranslation import SVGTranslationService
from CopySVGTranslation.core.mapping import InjectorData
from CopySVGTranslation.utils.xml import extract_root_languages


def write_svg(tmp_path: Path, content: str) -> Path:
    svg_path = tmp_path / "sample.svg"
    svg_path.write_text(textwrap.dedent(content), encoding="utf-8")
    return svg_path


def test_inject_tracks_new_languages(tmp_path):
    svg_path = write_svg(
        tmp_path,
        """
        <svg xmlns=\"http://www.w3.org/2000/svg\">
            <switch>
                <text id=\"t1\"><tspan>Hello</tspan></text>
            </switch>
        </svg>
        """,
    )

    mapping = {"new": {"hello": {"ar": "مرحبا", "fr": "Bonjour"}}}

    service = SVGTranslationService()
    result = service.inject(svg_path=svg_path, mapping=mapping, output=svg_path)

    assert result.success
    assert isinstance(result.data, InjectorData)
    stats = result.data.inject_stats.to_json()

    tree = result.data.tree
    assert tree is not None
    root = tree.getroot()
    after_languages = extract_root_languages(root)

    assert after_languages == {"ar", "fr"}
    assert stats["all_languages_count"] == 2
    assert stats["new_languages_count"] == 2
    assert stats["languages_after"] == ["ar", "fr"]


def test_inject_tracks_only_truly_new_languages(tmp_path):
    svg_path = write_svg(
        tmp_path,
        """
        <svg xmlns=\"http://www.w3.org/2000/svg\">
            <switch>
                <text id=\"t1\"><tspan>Hello</tspan></text>
                <text id=\"t1-ar\" systemLanguage=\"ar\"><tspan>مرحبا</tspan></text>
            </switch>
        </svg>
        """,
    )

    mapping = {"new": {"hello": {"ar": "مرحبا جديد", "fr": "Bonjour"}}}

    service = SVGTranslationService()
    result = service.inject(svg_path=svg_path, mapping=mapping, output=svg_path)

    assert result.success
    stats = result.data.inject_stats.to_json()

    assert stats["all_languages_count"] == 2
    assert stats["new_languages_count"] == 1
    assert stats["languages_after"] == ["fr"]


def test_file_langs_handles_element_tree(tmp_path):
    svg_path = write_svg(
        tmp_path,
        """
        <svg xmlns=\"http://www.w3.org/2000/svg\">
            <switch>
                <text id=\"t1\"><tspan>Hello</tspan></text>
            </switch>
        </svg>
        """,
    )

    service = SVGTranslationService()
    result = service.inject(
        svg_path=svg_path,
        mapping={"new": {"hello": {"ar": "مرحبا"}}},
        output=svg_path,
    )

    assert result.success
    tree = result.data.tree
    assert tree is not None

    root = tree.getroot()
    after_languages = extract_root_languages(root)
    assert after_languages == {"ar"}
