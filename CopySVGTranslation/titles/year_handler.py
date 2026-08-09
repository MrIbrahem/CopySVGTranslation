# titles/year_handler.py
from __future__ import annotations

import logging
import re
from typing import Any

from ..config import TranslationConfig
from ..core.mapping import TranslationMapping

logger = logging.getLogger(__name__)

YEAR_RE = re.compile(r"\d{4}")


class YearTitleHandler:
    """
    Unified handler for titles that contain a 4-digit year.

    Controlled by config.enable_year_titles.
    """

    def __init__(self, config: TranslationConfig | None = None) -> None:
        self.config = config or TranslationConfig()
        self.enabled = self.config.enable_year_titles

    # ------------------------------------------------------------------
    # Low-level helpers
    # ------------------------------------------------------------------
    @staticmethod
    def match_year(text: str) -> str:
        """
        Return the 4-digit year if it appears at the start or end of the
        string (after stripping), otherwise empty string.
        """
        text = text.strip()
        if len(text) < 4:
            return ""
        if text[-4:].isdigit():
            return text[-4:]
        if text[:4].isdigit():
            return text[:4]
        return ""

    def bulid_lang_template(self, value: str, lang: str) -> str:
        """
        "dag": "Parkinson's doro yɔlibu biɛɣigu ni, yuuni 1990 puli ni",
        "ca": "Prevalència de la malaltia de Parkinson",
        """
        if re.sub(r"\d{4}", "", value) == value:
            return f"{value}, {{year}}"

        if lang == "dag" and "," in value:
            value = value.split(",", maxsplit=1)[0]
            return self.bulid_lang_template(value, "")

        return ""

    @staticmethod
    def replace_year_with_placeholder(text: str, year: str) -> str:
        """
        Replace the year at the start or end with '{year}'.
        Returns empty string if the year is not in the expected position.
        """
        text = text.strip()

        if text.endswith(year):
            return re.sub(r"\d{4}$", "{year}", text)

        if text.startswith(year):
            return re.sub(r"^\d{4}", "{year}", text)

        return ""

    @staticmethod
    def apply_year(template: str, year: str) -> str:
        """Replace '{year}' placeholder with a concrete year."""
        return template.replace("{year}", year)

    # ------------------------------------------------------------------
    # Extraction side
    # ------------------------------------------------------------------

    def process_header_titles(self, mapping: TranslationMapping) -> bool:
        """
        Extract titles with years from mapping.meta['header'], template them,
        strip their years, and merge the year-free translations into mapping.new.
        Respects enable_year_titles (self.enabled) and config.create_lang_template.
        Returns True if mapping.new was modified.
        """
        if not self.enabled:
            return False

        if not self.config.create_lang_template:
            return False

        header = mapping.meta.get("header", {})
        if not header:
            return False

        extra_titles_new = self.build_title_new_templates(header, create_lang_template=True)
        if not extra_titles_new:
            return False

        # Create new object with new titles, so we don't modify the original title_new or overwrite it
        new_object = TranslationMapping.from_any({"title_new": extra_titles_new})

        from .year_stripper import merge_year_free_into_new
        changed = merge_year_free_into_new(new_object)

        if not changed:
            return False

        # Merge translations per-key, preserving existing language translations
        mapping.merge(new_object, merge_keys=["new"])
        return True

    def build_templates(self, mapping: TranslationMapping) -> None:
        """
        Populate mapping.title_new from mapping.new.

        Example
            -------
            Input (mapping.new):
            "COVID-19 pandemic 2020": {"ar": "جائحة كوفيد 2020", ...}

            Output (mapping.title_new):
            "COVID-19 pandemic {year}": {"ar": "جائحة كوفيد {year}", ...}
        """
        if not self.enabled:
            return

        data = self.build_title_new_templates(mapping.new)
        if data:
            mapping.title_new.update(data)

    def build_title_new_templates(
        self, mapping_new: dict[str, Any], create_lang_template: bool = False
    ) -> dict[str, Any]:
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
        data = {}
        for source, translations in list(mapping_new.items()):
            year = self.match_year(source)

            # if not year:
            if not source or source == year or not year.isdigit():
                continue

            source_template = self.replace_year_with_placeholder(source, year)
            if not source_template:
                continue

            templated: dict[str, str] = {}
            for lang, value in translations.items():
                value_template = self.replace_year_with_placeholder(value, year)
                if create_lang_template and not value_template:
                    value_template = self.bulid_lang_template(value, lang)

                if value_template:
                    templated[lang] = value_template

            if templated:
                data[source_template] = templated
                logger.debug("Title template: %r → %s", source_template, list(templated))
        return data

    # ------------------------------------------------------------------
    # Injection side
    # ------------------------------------------------------------------
    def expand_for_texts(
        self,
        mapping: TranslationMapping,
        default_texts: list[str],
        *,
        case_insensitive: bool = True,
    ) -> dict[str, dict[str, str]]:
        """
        Given the default (fallback) texts of a switch, return extra
        translation entries that should be merged into the working map.

        Example
        -------
        mapping.title_new = {
            "COVID-19 pandemic {year}": {"ar": "جائحة كوفيد {year}"}
            }
        default_texts = ["COVID-19 pandemic 1990"]

        Returns:
            {
            "COVID-19 pandemic 1990": {"ar": "جائحة كوفيد 1990"}
            }
        """
        if not self.enabled or not mapping.title_new:
            return {}

        # Normalize keys for lookup
        templates = {(k.strip().lower() if case_insensitive else k): v for k, v in mapping.title_new.items()}

        expanded: dict[str, dict[str, str]] = {}

        for text in default_texts:
            year = self.match_year(text)
            if not year:
                continue

            template_key = self.replace_year_with_placeholder(text, year)
            if not template_key:
                continue

            lookup = template_key.lower() if case_insensitive else template_key
            trans_templates = templates.get(lookup)
            if not trans_templates:
                continue

            expanded[text] = {lang: self.apply_year(tmpl, year) for lang, tmpl in trans_templates.items()}

        return expanded

    def enrich_mapping_for_switch(
        self,
        mapping: TranslationMapping,
        default_texts: list[str],
        *,
        case_insensitive: bool = True,
    ) -> TranslationMapping:
        """
        Return a *new* working mapping that includes expanded year titles
        for the given default texts. Does not mutate the original.
        """
        extra = self.expand_for_texts(
            mapping,
            default_texts,
            case_insensitive=case_insensitive,
        )
        if not extra:
            return mapping

        # Shallow copy + merge the extra entries into .new
        working = TranslationMapping.from_any(mapping.to_json())
        for source, trans in extra.items():
            key = source.lower() if case_insensitive else source
            working.new.setdefault(key, {}).update(trans)
        return working


__all__ = [
    "YearTitleHandler",
]
