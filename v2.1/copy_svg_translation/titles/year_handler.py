# titles/year_handler.py
from __future__ import annotations

import logging
import re

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
    def build_templates(self, mapping: TranslationMapping) -> None:
        """
        Populate mapping.title_new (and optionally mapping.title) from
        mapping.new.

        Example
            -------
            Input (mapping.new):
            "COVID-19 pandemic 2020": {"ar": "جائحة كوفيد 2020", ...}

            Output (mapping.title_new):
            "COVID-19 pandemic {year}": {"ar": "جائحة كوفيد {year}", ...}
        """
        if not self.enabled:
            return

        for source, translations in list(mapping.new.items()):
            year = self.match_year(source)
            if not year:
                continue

            source_template = self.replace_year_with_placeholder(source, year)
            if not source_template:
                continue

            templated: dict[str, str] = {}
            for lang, value in translations.items():
                value_template = self.replace_year_with_placeholder(value, year)
                if value_template:
                    templated[lang] = value_template

            if templated:
                mapping.title_new[source_template] = templated
                logger.debug("Title template: %r → %s", source_template, list(templated))

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
        templates = {(k.lower() if case_insensitive else k): v for k, v in mapping.title_new.items()}

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
