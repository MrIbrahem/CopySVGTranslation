# legacy/__init__.py
# from .extract import extract
from .inject import inject_file_tree, inject_file_and_save

__all__ = [
    # "extract",
    "inject_file_and_save",
    "inject_file_tree",
]
