from .injection_utils import (
    generate_unique_id,
    load_all_mappings,
)
from .text import normalize_lang, normalize_text, split_lang_list
from .xml import (
    collect_ids,
    extract_root_languages,
    extract_text_from_node,
    file_langs,
    sort_switch_children,
    sort_switch_texts,
    tree_languages,
)

__all__ = [
    "sort_switch_children",
    "collect_ids",
    "normalize_lang",
    "extract_root_languages",
    "tree_languages",
    "file_langs",
    "sort_switch_texts",
    "generate_unique_id",
    "load_all_mappings",
    "normalize_text",
    "extract_text_from_node",
    "split_lang_list",
]
