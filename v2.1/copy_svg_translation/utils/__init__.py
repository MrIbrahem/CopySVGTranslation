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
    "SVG_NS",
    "SVG_NSMAP",
    "collect_ids",
    "extract_text_segments",
    "findall_svg",
    "get_text_content",
    "is_svg_element",
    "local_name",
    "normalize_lang",
    "normalize_text",
    "sort_switch_children",
    "split_lang_list",
    "svg_tag",
    "tree_languages",
    "xpath_svg",
]
