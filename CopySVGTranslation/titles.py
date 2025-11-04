import logging
from typing import Dict, List

logger = logging.getLogger("CopySVGTranslation")


def make_title_translations(
    new: Dict[str, Dict[str, str]]
) -> Dict[str, Dict[str, str]]:
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
                "COVID-19 pandemic": {"ar": "جائحة كوفيد", "es": "Pandemia de COVID-19"}
            }

    Args:
        new: A dictionary mapping full titles (ending with a year) to their translations.

    Returns:
        A dictionary mapping base title -> { language -> title without year }.
    """
    all_mappings_title: Dict[str, Dict[str, str]] = {}

    new_fixed = {
        x.strip(): {z.strip(): h.strip() for z, h in v.items()}
        for x, v in new.items()
    }

    for key, mapping in list(new_fixed.items()):
        if len(key) < 5:
            continue
        year = key[-4:]
        if not key or key == year or not year.isdigit():
            continue

        data = {
            lang: value[:-4].strip()
            for lang, value in mapping.items()
            if len(value) > 4 and value[-4:] == year
        }
        if data:
            all_mappings_title[key[:-4].strip()] = data

    return all_mappings_title


def get_titles_translations(
    all_mappings_title: Dict[str, Dict[str, str]],
    default_texts: List[str],
) -> Dict[str, Dict[str, str]]:
    """
    Build reconstructed translations by reattaching the year to the base titles.

    Example:
        Input:
            all_mappings_title = {
                "COVID-19 pandemic": {"ar": "جائحة كوفيد", "es": "Pandemia de COVID-19"}
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

    all_mappings_title_fixed = {
        x.strip().lower(): v for x, v in all_mappings_title.items()
    }

    for text in default_texts:
        if len(text) > 4 and text[-4:].isdigit():
            year = text[-4:]
            key = text[:-4]
            translations = all_mappings_title_fixed.get(key.strip().lower())
            if translations:
                titles_translations[text] = {lang: f"{value} {year}" for lang, value in translations.items()}

    return titles_translations
