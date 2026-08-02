from .elements_utils import (
    extract_root_languages,
    file_langs,
    sort_switch_texts,
    tree_langs,
)
from .injection_utils import (
    generate_unique_id,
    get_target_path,
    load_all_mappings,
)
from .text_utils import extract_text_from_node, normalize_text

__all__ = [
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
