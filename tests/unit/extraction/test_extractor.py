# ruff: noqa: F401
"""
Unit tests for CopySVGTranslation/extraction/extractor.py module.

Functions to test: get_english_default_texts, extract

TODO: write tests
"""


from pathlib import Path

from CopySVGTranslation.extraction.extractor import (
    extract,
    get_english_default_texts,
)


FIXTURES_DIR = Path(__file__).parent.parent.parent

def test_extract_with_string_path() -> None:
    """extract should work with string paths."""
    source_path = str(FIXTURES_DIR / "Parkinsons disease prevalence ihme, World, 1990.svg")

    result = extract(source_path)

    assert result is not None
    assert isinstance(result, dict)
