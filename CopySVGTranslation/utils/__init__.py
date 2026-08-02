from .elements_utils import (
    extract_root_languages,
    extract_text_from_node,
    file_langs,
    sort_switch_texts,
    tree_langs,
)
from .injection_utils import (
    generate_unique_id,
    get_target_path,
    load_all_mappings,
)
from .text_utils import normalize_lang, normalize_text

__all__ = [
    "normalize_lang",
    "extract_root_languages",
    "tree_langs",
    "file_langs",
    "sort_switch_texts",
    "get_target_path",
    "generate_unique_id",
    "load_all_mappings",
    "normalize_text",
    "extract_text_from_node",
]
