# service.py
from __future__ import annotations

import logging
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from lxml import etree

from .switch_order_checker import SwitchOrderChecker

from .config import TranslationConfig
from .core.mapping import InjectorData, TranslationMapping
from .extraction.extractor import SVGTranslationExtractor
from .injection.injector import SVGTranslationInjector
from .io.mapping_store import MappingStore
from .io.output_paths import resolve_svg_output_path
from .io.svg_writer import write_svg
from .nested import NestedStructureService
from .result import OperationResult

logger = logging.getLogger(__name__)


class SVGTranslationService:
    """
    Main public facade for SVG translation extraction and injection.

    All high-level operations go through this class.
    Low-level components (extractor, injector, preparer, etc.) are
    created internally from the supplied TranslationConfig.
    """

    def __init__(self, config: TranslationConfig | None = None) -> None:
        self.config = config or TranslationConfig()
        self._extractor = SVGTranslationExtractor(self.config)
        self._injector = SVGTranslationInjector(self.config)
        self._mapping_store = MappingStore(self.config)
        self.switch_order_checker = SwitchOrderChecker(self.config)
        self._nested = NestedStructureService(
            strategy=self.config.nested_strategy,
            also_fix_a=True,
            config=self.config,
        )

    # ------------------------------------------------------------------
    # Public API for nested
    # ------------------------------------------------------------------

    def analyze_nested(
        self,
        svg_path: Path | str,
    ) -> OperationResult[list[str]]:
        """
        Detect nested tspan/a structures. Read-only.
        """
        try:
            findings = self._nested.analyze_file(Path(svg_path))
            return OperationResult.ok(data=findings)
        except Exception as exc:
            return OperationResult.fail(
                error=str(exc),
                error_code=getattr(exc, "code", "nested_analyze_error"),
            )

    def repair_nested(
        self,
        svg_path: Path | str,
        *,
        output: Path | str | None = None,
        strategy: Any = None,  # Can be NestedStrategy or None
        save: bool = True,
    ) -> OperationResult:
        """
        Repair nested structures and optionally save.
        Does NOT run as part of extract/inject.
        """
        if save and output is None:
            return OperationResult.fail(
                error="save=True but no output path",
                error_code="missing_output_path",
            )
        try:
            resolved_output = self._resolve_output_path(output) if output else None
            result = self._nested.repair_file(
                source=Path(svg_path),
                output=resolved_output,
                strategy=strategy or self.config.nested_strategy,
                save=save,
            )
            if not result.success:
                return OperationResult.fail(
                    error="; ".join(result.warnings) if result.warnings else "Repair failed",
                    error_code="nested_repair_error",
                )
            return OperationResult.ok(data=result)
        except Exception as exc:
            return OperationResult.fail(
                error=str(exc),
                error_code=getattr(exc, "code", "nested_repair_error"),
            )

    # ------------------------------------------------------------------
    # Public API for extract and inject
    # ------------------------------------------------------------------

    def extract(
        self,
        svg_path: Path | str,
        *,
        save_mapping: bool | Path | None = None,
    ) -> OperationResult[TranslationMapping]:
        """
        Extract translations from an SVG file.

        Parameters
        ----------
        svg_path:
            Source SVG file.
        save_mapping:
            - None / False → do not save
            - True → save to config.mapping_output_dir / <name>.json
            - Path → save to the given path

        Returns
        -------
        OperationResult[TranslationMapping]
        """
        svg_path = Path(svg_path)

        try:
            mapping = self._extractor.extract(svg_path)
        except Exception as exc:
            logger.exception("Extraction failed for %s", svg_path)
            return OperationResult.fail(
                error=str(exc),
                error_code=getattr(exc, "code", "extraction_error"),
            )

        if not mapping or mapping.is_empty():
            return OperationResult.fail(
                error="No translations found or file could not be parsed",
                error_code="no_translations",
            )

        warnings: list[str] = []

        if save_mapping:
            try:
                out = self._resolve_mapping_output(svg_path, save_mapping)
                self._mapping_store.save(mapping, out)
            except (OSError, Exception) as exc:
                warnings.append(f"Failed to save mapping: {exc}")

        return OperationResult.ok(data=mapping, warnings=warnings)

    def inject(
        self,
        svg_path: Path | str,
        mapping: TranslationMapping | Mapping[str, Any],
        *,
        output: Path | str | None = None,
        save: bool | None = None,
    ) -> OperationResult:
        """
        Inject translations into an SVG file.

        Parameters
        ----------
        svg_path:
            Target SVG to inject into.
        mapping:
            TranslationMapping or a raw dict compatible with it.
        output:
            Destination path. Required when saving.
        save:
            Override config.auto_save. If None, uses config.auto_save.

        Returns
        -------
        OperationResult[InjectorData]
        """
        svg_path = Path(svg_path)
        should_save = self.config.auto_save if save is None else save

        if should_save and output is None:
            return OperationResult.fail(
                error="save=True but no output path provided",
                error_code="missing_output_path",
            )

        try:
            normalized = TranslationMapping.from_any(mapping)
            resolved_output = self._resolve_output_path(output) if output else None
            injector_data: InjectorData = self._injector.inject(
                svg_path,
                normalized,
                save_path=resolved_output,
                save=should_save,
            )
        except Exception as exc:
            logger.exception("Injection failed for %s", svg_path)
            return OperationResult.fail(
                error=str(exc),
                error_code=getattr(exc, "code", "injection_error"),
            )

        if injector_data.tree is None:
            return OperationResult.fail(
                error=injector_data.error.label or "Injection returned no tree",
                error_code=injector_data.error.code or "injection_failed",
                stats=injector_data.inject_stats,
            )

        return OperationResult.ok(data=injector_data, stats=injector_data.inject_stats)

    def extract_and_inject(
        self,
        source: Path | str,
        output: Path | str,
        *,
        save_mapping: bool | Path | None = None,
        save: bool | None = None,
    ) -> OperationResult:
        """Extract translations from ``source`` and apply them to ``output``.

        ``output`` is the one target file for the workflow: it is read as the
        SVG to modify and, when saving is enabled, overwritten with the
        translated result. ``config.output_dir`` is intentionally not applied
        to this in-place workflow. This avoids a separate target/input path and
        output/destination path for the same operation.
        """
        extract_result = self.extract(source, save_mapping=save_mapping)
        if not extract_result.success or extract_result.data is None:
            return OperationResult.fail(
                error=extract_result.error or "Extraction failed",
                error_code=extract_result.error_code,
                warnings=extract_result.warnings,
            )

        # Use an absolute path so inject() does not reinterpret a bare output
        # filename through config.output_dir. This workflow always saves in place.
        output_path = Path(output).absolute()
        inject_result = self.inject(
            output_path,
            extract_result.data,
            output=output_path,
            save=save,
        )

        # Merge warnings from extract_result into inject_result
        merged_warnings = extract_result.warnings + inject_result.warnings
        if inject_result.success:
            return OperationResult.ok(
                data=inject_result.data,
                stats=inject_result.stats,
                warnings=merged_warnings,
            )

        return OperationResult.fail(
            stats=inject_result.stats,
            error=inject_result.error,
            error_code=inject_result.error_code,
            warnings=merged_warnings,
        )

    def check_switches_sorted(
        self,
        svg_path: Path | str,
    ) -> OperationResult[bool]:
        """Check whether every <switch> in the file is already sorted.

        Returns ``True`` when all switches are sorted. If ``False``, call
        :meth:`sort_switches` to fix and re-upload to commons.
        """
        try:
            result = self.switch_order_checker.are_switches_sorted(svg_path)
            return OperationResult.ok(data=result)
        except Exception as exc:
            return OperationResult.fail(
                error=str(exc),
                error_code=getattr(exc, "code", "check_sorted_error"),
            )

    def sort_switches(
        self,
        svg_path: Path | str,
        *,
        output: Path | str | None = None,
    ) -> OperationResult[bool]:
        """Sort every <switch> in the file and optionally save it.

        Returns ``True`` if the file was modified (was not already sorted).
        """
        try:
            resolved_output = self._resolve_output_path(output) if output else None
            modified = self.switch_order_checker.sort_switches(
                svg_path, save_path=resolved_output
            )
            return OperationResult.ok(data=modified)
        except Exception as exc:
            return OperationResult.fail(
                error=str(exc),
                error_code=getattr(exc, "code", "sort_switches_error"),
            )

    def prepare_only(
        self,
        svg_path: Path | str,
        *,
        output: Path | str | None = None,
    ) -> OperationResult[etree._ElementTree]:
        """
        Run only the preparation pipeline (normalize structure, IDs,
        language splitting, etc.) without injecting any translations.
        Useful for cleaning SVGs before manual translation or other tools.
        """
        svg_path = Path(svg_path)

        try:
            tree = self._injector.prepare(svg_path)
            if output:
                resolved_output = self._resolve_output_path(output)
                write_svg(tree, resolved_output, config=self.config)
            return OperationResult.ok(data=tree)
        except Exception as exc:
            return OperationResult.fail(
                error=str(exc),
                error_code=getattr(exc, "code", "prepare_error"),
            )

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def load_mapping(self, path: Path | str) -> OperationResult[TranslationMapping]:
        """Load a previously saved JSON mapping file."""
        try:
            mapping = self._mapping_store.load(Path(path))
            return OperationResult.ok(data=mapping)
        except Exception as exc:
            return OperationResult.fail(error=str(exc), error_code="load_mapping_error")

    def save_mapping(
        self,
        mapping: TranslationMapping,
        path: Path | str,
    ) -> OperationResult[Path]:
        """Save a mapping to JSON."""
        path = Path(path)
        try:
            self._mapping_store.save(mapping, path)
            return OperationResult.ok(data=path)
        except Exception as exc:
            return OperationResult.fail(error=str(exc), error_code="save_mapping_error")

    # ------------------------------------------------------------------
    # Internal helpers (lazy collaborators)
    # ------------------------------------------------------------------

    def _resolve_output_path(self, output: Path | str) -> Path:
        """
        Resolve output path for SVG files, applying output_dir only when
        the given path is a bare filename (no directory component).
        """
        return resolve_svg_output_path(output, config=self.config)

    def _resolve_mapping_output(
        self,
        svg_path: Path,
        save_mapping: bool | Path,
    ) -> Path:
        if isinstance(save_mapping, str | Path):
            return Path(save_mapping)

        return self._mapping_store.default_mapping_path(svg_path)


__all__ = [
    "SVGTranslationService",
]
