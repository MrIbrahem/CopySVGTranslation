**Package Root `__init__.py` — Public API**

```python
# CopySVGTranslation/__init__.py
"""
CopySVGTranslation
------------------
Extract translations from SVG files and inject them into others.

Modern entry point:
    from CopySVGTranslation import SVGTranslationService, TranslationConfig

Legacy functions (deprecated):
    from CopySVGTranslation import extract, inject
"""

from __future__ import annotations

__version__ = "2.0.0"

# ---------------------------------------------------------------------------
# Primary public API
# ---------------------------------------------------------------------------
from .config import TranslationConfig
from .service import SVGTranslationService

from .result import OperationResult, InjectorStats
from .core.mapping import TranslationMapping, TranslationEntry

from .exceptions import (
    CopySVGTranslationError,
    SvgStructureError,
    SvgNestedTspanError,
    SvgParseError,
    SvgIOError,
    MappingError,
    ConfigurationError,
)

# ---------------------------------------------------------------------------
# Optional advanced exports (still public, but less commonly needed)
# ---------------------------------------------------------------------------
from .extraction import SVGTranslationExtractor
from .injection import SVGTranslationInjector, SvgPreparationPipeline
from .titles import YearTitleHandler
from .nested import NestedTspanDetector, NestedTspanFlattener
from .io import SvgDocument, MappingStore

# ---------------------------------------------------------------------------
# Legacy compatibility layer (deprecated)
# ---------------------------------------------------------------------------
from .legacy import extract, inject, svg_extract_and_inject

__all__ = [
    # version
    "__version__",
    # main facade
    "SVGTranslationService",
    "TranslationConfig",
    # results & data
    "OperationResult",
    "InjectorStats",
    "TranslationMapping",
    "TranslationEntry",
    # exceptions
    "CopySVGTranslationError",
    "SvgStructureError",
    "SvgNestedTspanError",
    "SvgParseError",
    "SvgIOError",
    "MappingError",
    "ConfigurationError",
    # advanced
    "SVGTranslationExtractor",
    "SVGTranslationInjector",
    "SvgPreparationPipeline",
    "YearTitleHandler",
    "NestedTspanDetector",
    "NestedTspanFlattener",
    "SvgDocument",
    "MappingStore",
    # legacy (deprecated)
    "extract",
    "inject",
    "svg_extract_and_inject",
]
```

---

### What users are expected to import

**Recommended (new code):**

```python
from CopySVGTranslation import (
    SVGTranslationService,
    TranslationConfig,
    OperationResult,
    TranslationMapping,
)
```

**Advanced / library integration:**

```python
from CopySVGTranslation import (
    SVGTranslationExtractor,
    SVGTranslationInjector,
    SvgPreparationPipeline,
    YearTitleHandler,
    NestedTspanFlattener,
    SvgDocument,
    MappingStore,
)
```

**Legacy (still works, emits deprecation warnings):**

```python
from CopySVGTranslation import extract, inject, svg_extract_and_inject
```

---

### Design choices

| Choice                                            | Reason                                                                |
| ------------------------------------------------- | --------------------------------------------------------------------- |
| Service + Config first                            | Clear modern entry point                                              |
| `OperationResult` + `TranslationMapping` exported | Needed to use the service effectively                                 |
| Exceptions exported at top level                  | Callers can catch specific errors easily                              |
| Advanced classes still public                     | Power users and tests can reach them without deep imports             |
| Legacy kept in `__all__` for now                  | Backward compatibility during migration                               |
| Explicit `__all__`                                | Controls `from CopySVGTranslation import *` and documents the surface |

---

### After Phase 3 (cleanup)

Once legacy is removed, the bottom section becomes:

```python
# No legacy exports
__all__ = [
    "__version__",
    "SVGTranslationService",
    "TranslationConfig",
    "OperationResult",
    "InjectorStats",
    "TranslationMapping",
    "TranslationEntry",
    "CopySVGTranslationError",
    "SvgStructureError",
    "SvgNestedTspanError",
    "SvgParseError",
    "SvgIOError",
    "MappingError",
    "ConfigurationError",
    "SVGTranslationExtractor",
    "SVGTranslationInjector",
    "SvgPreparationPipeline",
    "YearTitleHandler",
    "NestedTspanDetector",
    "NestedTspanFlattener",
    "SvgDocument",
    "MappingStore",
]
```

This is the stable public face of the redesigned package.
