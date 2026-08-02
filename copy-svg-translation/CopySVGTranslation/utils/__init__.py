# utils/__init__.py
from .text import normalize_lang, normalize_text, split_lang_list
from .xml import (
    SVG_NS,
    SVG_NSMAP,
    collect_ids,
    extract_text_segments,
    findall_svg,
    get_text_content,
    is_svg_element,
    local_name,
    sort_switch_children,
    svg_tag,
    tree_languages,
    xpath_svg,
)

__all__ = [
    "normalize_text",
    "normalize_lang",
    "split_lang_list",
    "SVG_NS",
    "SVG_NSMAP",
    "svg_tag",
    "local_name",
    "is_svg_element",
    "findall_svg",
    "xpath_svg",
    "extract_text_segments",
    "get_text_content",
    "collect_ids",
    "sort_switch_children",
    "tree_languages",
]
