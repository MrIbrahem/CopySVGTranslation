from .text import normalize_lang, normalize_text, split_lang_list
from .xml import (
    SVG_NS,
    SVG_NSMAP,
    are_switches_sorted,
    collect_ids,
    extract_root_languages,
    findall_svg,
    is_svg_element,
    is_switch_sorted,
    local_name,
    sort_switch_children,
    sort_switch_texts,
    svg_tag,
    tree_languages,
    xpath_svg,
)

__all__ = [
    # text
    "normalize_text",
    "normalize_lang",
    "split_lang_list",
    # xml
    "SVG_NS",
    "SVG_NSMAP",
    "svg_tag",
    "local_name",
    "is_svg_element",
    "findall_svg",
    "xpath_svg",
    "collect_ids",
    "extract_root_languages",
    "tree_languages",
    "sort_switch_children",
    "sort_switch_texts",
    "is_switch_sorted",
    "are_switches_sorted",
]
