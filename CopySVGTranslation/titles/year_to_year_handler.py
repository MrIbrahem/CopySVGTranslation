from __future__ import annotations

from dataclasses import dataclass
import logging
import re
from typing import Any

from ..config import TranslationConfig
from ..core.mapping import TranslationMapping

logger = logging.getLogger(__name__)

@dataclass
class TitleYearMapping:
    source: str
    source_template: str
    year1: str
    year2: str

class YearTitleHandlerNew:
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
    def match_years(text: str) -> tuple[str, str]:
        """
        match <year1> to <year2> if it appears at the start or end of the text
        Example: wine production, 1961 to 2023
        """
        text = text.strip()

        m = re.search(r" (\d{4})\s+to\s+(\d{4})$", text)
        if m:
            return m.group(1), m.group(2)

        return "", ""

    @staticmethod
    def replace_years_with_placeholder(text: str, year1: str, year2: str, lang: str = "en") -> str:
        text = text.strip()

        en_text = f"{year1} to {year2}"
        if lang == "en" and en_text in text:
            return text.replace(en_text, "{year1} to {year2}")

        ar_text = f"{year1} إلى {year2}"
        if lang == "ar" and ar_text in text:
            return text.replace(ar_text, "{year1} إلى {year2}")

        if year1 in text and year2 in text:
            return text.replace(year1, "{year1}").replace(year2, "{year2}")

        return ""

    def extend_translations(
        self,
        one_year_translations: dict[str, str],
    ) -> dict[str, str]:
        """
        Extend translations with year placeholders.

        one_year_translations example:
            - {"ar": "إنتاج النبيذ، {year}"}

        """
        langs_data = {
            "ar": ("، {year}", "، {year1} إلى {year2}")
        }

        data = {}

        for lang, (one_year, years_str) in langs_data.items():
            lang_value = one_year_translations.get(lang)
            if not lang_value:
                continue

            if one_year in lang_value:
                data[lang] = lang_value.replace(one_year, years_str)

        return data

    def build_templates(self, mapping: TranslationMapping) -> None:
        """
        Populate mapping.title_new from mapping.new.
        """
        if not self.enabled:
            return

        data = self.build_title_new_templates_year1_to_year2(mapping)
        if data:
            mapping.title_new.update(data)

    def build_title_new_templates_year1_to_year2(
        self,
        mapping: TranslationMapping,
        set_key_with_empty_value: bool | None = None,
    ) -> dict[str, Any]:
        """
        Extract valid title translations by verifying that all translations in a mapping
        end with the same 4-digit year as the key.

        Example:
            Input:
                mapping.new = {
                    "Wine production, 1961 to 2023": {"ar": "إنتاج النبيذ، 1961 إلى 2023"}
                }
                OR
                mapping.new = {
                    "wine production, 1961 to 2023": {},
                }
                mapping.title_new = {
                    "wine production, {year}": {"ar": "إنتاج النبيذ، {year}"}
                }
            Output:
                {
                    "wine production, {year1} to {year2}": {"ar": "إنتاج النبيذ، {year1} إلى {year2}"}
                }

        Args:
            new: A dictionary mapping full titles (ending with a year) to their translations.

        Returns:
            A dictionary mapping base title -> { language -> title with `{year}` }.
        """
        if set_key_with_empty_value is None:
            set_key_with_empty_value = self.config.set_key_with_empty_value

        en_keys_to_work: list[TitleYearMapping] = []

        for source in mapping.new.keys():
            source = source.strip()

            if not source or source.isdigit():
                continue

            year1, year2 = self.match_years(source)

            # if not year:
            if not year1.isdigit() or not year2.isdigit():
                continue

            source_template = self.replace_years_with_placeholder(source, year1, year2, "en")
            if not source_template:
                continue

            map = TitleYearMapping(
                source=source,
                source_template=source_template,
                year1=year1,
                year2=year2
            )
            en_keys_to_work.append(map)

        data = {}
        for map in en_keys_to_work:
            translations = mapping.new[map.source]
            sub_source = map.source.replace("{year1} to {year2}", "{year}")

            templated: dict[str, str] = {}

            if sub_source in mapping.title_new:
                sub_data = {x:v for x, v in mapping.title_new[sub_source].items() if x not in translations}
                templated = self.extend_translations(sub_data)

            if translations:
                for lang, value in translations.items():
                    value_template = self.replace_years_with_placeholder(value, map.year1, map.year2, lang=lang)

                    if value_template:
                        templated[lang] = value_template

            if templated or set_key_with_empty_value:
                data[map.source_template] = templated
                logger.debug("Title template: %r → %s", map.source_template, list(templated))

        return data

__all__ = [
    "YearTitleHandlerNew",
]
