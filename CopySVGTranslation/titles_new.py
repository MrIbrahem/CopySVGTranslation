import logging
import re
from typing import Dict, List

logger = logging.getLogger("CopySVGTranslation")


def match_year(text):
    """
    match and return 4 digit year at the end or start of a string
    """
    text = text.strip()
    if len(text) < 4:
        return ""

    if text[-4:].isdigit():
        return text[-4:]

    if text[:4].isdigit():
        return text[:4]

    return ""


def replace_year(value, year):
    # if value.count(year) == 1:

    if value.endswith(year):
        return re.sub(r"\d{4}$", "{year}", value)

    if value.startswith(year):
        return re.sub(r"^\d{4}", "{year}", value)
    return ""


def make_new_title_translations(new: Dict[str, Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    """
    Extract valid title translations by verifying that all translations in a mapping
    end with the same 4-digit year as the key.

    Example:
        Input:
            {
                "COVID-19 pandemic 2020": {"ar": "جائحة كوفيد 2020", "es": "Pandemia de COVID-19 2020"}
            }
        Output:
            {
                "COVID-19 pandemic {year}": {"ar": "جائحة كوفيد {year}", "es": "Pandemia de COVID-19 {year}"}
            }

    Args:
        new: A dictionary mapping full titles (ending with a year) to their translations.

    Returns:
        A dictionary mapping base title -> { language -> title with `{year}` }.
    """

    result: Dict[str, Dict[str, str]] = {}

    new_fixed = {x.strip(): {z.strip(): h.strip() for z, h in v.items()} for x, v in new.items()}

    for key, mapping in list(new_fixed.items()):
        if len(key) < 4:
            continue

        year = match_year(key)
        if not key or key == year or not year.isdigit():
            continue

        data = {}
        en_key = replace_year(key, year)
        if not en_key:
            continue
        for lang, value in mapping.items():
            new_str = replace_year(value, year)
            if new_str:
                data[lang] = new_str

        if data:
            result[en_key] = data

    return result


def get_new_titles_translations(
    all_mappings_title: Dict[str, Dict[str, str]],
    default_texts: List[str],
) -> Dict[str, Dict[str, str]]:
    """
    Build reconstructed translations by reattaching the year to the base titles.

    Example:
        Input:
            all_mappings_title = {
                "COVID-19 pandemic {year}": {"ar": "جائحة كوفيد {year}", "es": "Pandemia de COVID-19 {year}"}
            }
            default_texts = ["COVID-19 pandemic 1990"]
        Output:
            {
                "COVID-19 pandemic 1990": {"en": "COVID-19 pandemic 1990", "es": "Pandemia de COVID-19 1990"}
            }

    Args:
        all_mappings_title: Dictionary from year -> translations without year.
        default_texts: List of default titles (with years) to reconstruct translations for.

    Returns:
        Dictionary mapping original title -> translations including the year.
    """
    titles_translations: Dict[str, Dict[str, str]] = {}

    all_mappings_title_fixed = {x.strip().lower(): v for x, v in all_mappings_title.items()}

    for text in default_texts:
        year = match_year(text)
        if not year:
            continue
        en_key = replace_year(text, year)
        translations = all_mappings_title_fixed.get(en_key.strip().lower())
        if translations:
            titles_translations[text] = {lang: value.replace("{year}", year) for lang, value in translations.items()}

    return titles_translations
