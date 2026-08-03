# legacy/__init__.py
from .extract import extract
from .inject import inject_file_tree
from .workflows import svg_translate_between_files, svg_inject_translations

__all__ = [
    "extract",
    "inject_file_tree",
    "svg_translate_between_files",
    "svg_inject_translations",
]
