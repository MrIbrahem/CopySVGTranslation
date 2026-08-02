# utils/__init__.py
from .text import normalize_text, normalize_lang, split_lang_list
from .xml import (
    SVG_NS,
    SVG_NSMAP,
    svg_tag,
    local_name,
    is_svg_element,
    findall_svg,
    xpath_svg,
    extract_text_segments,
    get_text_content,
    collect_ids,
    sort_switch_children,
    tree_languages,
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
