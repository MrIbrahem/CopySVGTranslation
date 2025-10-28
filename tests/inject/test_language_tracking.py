import textwrap
from pathlib import Path

from CopySvgTranslate.injection.injector import file_langs, inject


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

    before_languages = set(file_langs(svg_path))
    mapping = {"new": {"hello": {"ar": "مرحبا", "fr": "Bonjour"}}}

    tree, stats = inject(
        svg_path,
        all_mappings=mapping,
        save_result=False,
        return_stats=True,
    )

    after_languages = set(file_langs(tree))

    assert before_languages == set()
    assert after_languages == {"ar", "fr"}
    assert stats["all_languages"] == 2
    assert stats["new_languages"] == 2
    assert stats["new_languages_list"] == ["ar", "fr"]


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

    _, stats = inject(
        svg_path,
        all_mappings=mapping,
        save_result=False,
        return_stats=True,
    )

    assert stats["all_languages"] == 2
    assert stats["new_languages"] == 1
    assert stats["new_languages_list"] == ["fr"]


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

    tree, _ = inject(
        svg_path,
        all_mappings={"new": {"hello": {"ar": "مرحبا"}}},
        save_result=False,
        return_stats=True,
    )

    assert set(file_langs(tree)) == {"ar"}
