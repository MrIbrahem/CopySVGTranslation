import logging

from ..core import TranslationMapping
from ..config import TranslationConfig
from .year_handler import YearTitleHandler

logger = logging.getLogger(__name__)

def get_new_titles_translations(
    all_mappings_title: dict[str, dict[str, str]],
    default_texts: list[str],
) -> dict[str, dict[str, str]]:
    """
    Extract valid title translations by verifying that all translations in a mapping
    end with the same 4-digit year as the key.
    """

    config = TranslationConfig(enable_year_titles=True)
    year_handler = YearTitleHandler(config)

    mapping = TranslationMapping(title_new=all_mappings_title)

    expanded = year_handler.expand_for_texts(
        mapping=mapping,
        default_texts=default_texts,
    )

    return expanded

__all__ = [
    "get_new_titles_translations",
]
