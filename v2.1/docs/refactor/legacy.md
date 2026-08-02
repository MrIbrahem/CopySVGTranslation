**Legacy Package Design**

```
legacy/
├── __init__.py
├── extract.py
├── inject.py
└── workflows.py
```

Purpose: keep old call sites working during migration, while clearly marking everything as deprecated and routing to the new class-based implementation.

---

### 1. `legacy/extract.py`

```python
# legacy/extract.py
from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any

from ..config import TranslationConfig
from ..service import SVGTranslationService


def extract(
    source_file: str | Path,
    case_insensitive: bool = True,
) -> dict[str, Any] | None:
    """
    Deprecated. Use SVGTranslationService.extract() instead.

    Legacy function-style wrapper kept for backward compatibility.
    Returns a plain dict (or None on failure), matching the old API.
    """
    warnings.warn(
        "copy_svg_translation.extract() is deprecated. "
        "Use SVGTranslationService.extract() instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    config = TranslationConfig(case_insensitive=case_insensitive)
    service = SVGTranslationService(config)
    result = service.extract(source_file)

    if not result.success or result.data is None:
        return None

    return result.data.to_dict()
```

---

### 2. `legacy/inject.py`

```python
# legacy/inject.py
from __future__ import annotations

import warnings
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from ..config import TranslationConfig
from ..core.mapping import TranslationMapping
from ..io.mapping_store import MappingStore
from ..service import SVGTranslationService
from ..utils.xml import tree_languages  # only if needed for stats shape


def inject(
    inject_file: Path | str | None = None,
    all_mappings: Mapping | None = None,
    case_insensitive: bool = True,
    save_path: Path | None = None,
    output_dir: Path | None = None,
    overwrite: bool = False,
    save_result: bool = False,
    return_stats: bool = False,
    pretty_print: bool | None = None,
) -> tuple[Any, Any] | Any:
    """
    Deprecated. Use SVGTranslationService.inject() instead.

    Legacy function-style wrapper kept for backward compatibility.
    """
    warnings.warn(
        "copy_svg_translation.inject() is deprecated. "
        "Use SVGTranslationService.inject() instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    # ---- normalize legacy argument aliases ----

    if inject_file is None:
        return (None, {"error": "No inject file provided"}) if return_stats else None

    # ---- resolve mapping ----
    if all_mappings is None and mapping_files:
        store = MappingStore()
        all_mappings = store.load_many(mapping_files).to_dict()

    if not all_mappings:
        return (None, {"error": "No valid mappings found"}) if return_stats else None

    # ---- resolve output path ----
    inject_path = Path(str(inject_file))
    target: Path | None = None
    if save_result:
        if save_path:
            target = Path(save_path)
        elif output_dir:
            target = Path(output_dir) / inject_path.name
        else:
            target = inject_path.parent / "translated" / inject_path.name

    # ---- call new service ----
    config = TranslationConfig(
        case_insensitive=case_insensitive,
        overwrite=overwrite,
        pretty_print=pretty_print,
        auto_save=False,
    )
    service = SVGTranslationService(config)

    result = service.inject(
        inject_path,
        TranslationMapping.from_any(all_mappings),
        output=target,
        save=save_result,
    )

    if return_stats:
        stats = result.stats.to_json() if result.stats else {}
        if not result.success:
            stats["error"] = result.error or "injection_failed"
        return result.data, stats

    return result.data
```

---

### 3. `legacy/workflows.py`

```python
# legacy/workflows.py
from __future__ import annotations

import warnings
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ..config import TranslationConfig
from ..service import SVGTranslationService


def svg_extract_and_inject(
    extract_file: Path | str,
    inject_file: Path | str,
    target_path: Path | None = None,
    all_mappings_file: Path | None = None,
    overwrite: bool | None = None,
    save_result: bool = False,
) -> Any:
    """
    Deprecated. Use SVGTranslationService.extract_and_inject() instead.
    """
    warnings.warn(
        "copy_svg_translation.svg_extract_and_inject() is deprecated. "
        "Use SVGTranslationService.extract_and_inject() instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    config = TranslationConfig(
        overwrite=bool(overwrite),
        auto_save=False,
    )
    service = SVGTranslationService(config)

    save_mapping: bool | Path | None = False
    if all_mappings_file is not None:
        save_mapping = Path(all_mappings_file)
    else:
        # old behaviour: always wrote a JSON under cwd/data/
        save_mapping = True

    result = service.extract_and_inject(
        source=extract_file,
        target=inject_file,
        output=target_path,
        save_mapping=save_mapping,
        save=save_result,
    )

    return result.data  # ElementTree or None


def svg_extract_and_injects(
    translations: Mapping,
    inject_file: Path | str,
    output_dir: Path | None = None,
    save_result: bool = False,
    overwrite: bool = False,
    pretty_print: bool | None = None,
) -> Any:
    """
    Deprecated. Use SVGTranslationService.inject() instead.
    """
    warnings.warn(
        "copy_svg_translation.svg_extract_and_injects() is deprecated. "
        "Use SVGTranslationService.inject() instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    from .inject import inject

    return inject(
        inject_file=inject_file,
        all_mappings=translations,
        output_dir=output_dir,
        save_result=save_result,
        overwrite=overwrite,
        pretty_print=pretty_print,
    )
```

---

### 4. `legacy/__init__.py`

```python
# legacy/__init__.py
from .extract import extract
from .inject import inject
from .workflows import svg_extract_and_inject, svg_extract_and_injects

__all__ = [
    "extract",
    "inject",
    "svg_extract_and_inject",
    "svg_extract_and_injects",
]
```

---

### Behaviour contract (what old callers still get)

| Old API                           | Still returns         | Notes                                                           |
| --------------------------------- | --------------------- | --------------------------------------------------------------- |
| `extract(path)`                   | `dict \| None`        | Same shape as old `to_json()`                                   |
| `inject(..., return_stats=False)` | `ElementTree \| None` | Same as before                                                  |
| `inject(..., return_stats=True)`  | `(tree, stats_dict)`  | `stats` includes `error` on failure                             |
| `svg_extract_and_inject(...)`     | `ElementTree \| None` | Still may write JSON if `all_mappings_file` or default path used |
| `svg_extract_and_injects(...)`    | same as `inject`      | Thin redirect                                                   |

All of them emit `DeprecationWarning`.

---

### Design principles

1. **No duplicated business logic** — every legacy function only adapts arguments and calls `SVGTranslationService`.
2. **Same return types as before** — dict / None / ElementTree / (tree, stats) so existing code does not break.
3. **Visible deprecation** — `warnings.warn(..., DeprecationWarning)`.
4. **Argument aliases preserved** — `source_file`, `translations`, etc. still accepted.
5. **Easy to delete** — in Phase 3, remove the `legacy/` package and drop the exports from the root `__init__.py`.

---

### Migration message for users

```text
DeprecationWarning: copy_svg_translation.extract() is deprecated.
Use SVGTranslationService.extract() instead.
```

Recommended replacement:

```python
from copy_svg_translation import SVGTranslationService, TranslationConfig

service = SVGTranslationService(TranslationConfig(case_insensitive=True))
result = service.extract("file.svg")
if result.success:
    mapping = result.data
```

This keeps the project usable during the transition while pushing new code toward the modern API.
