**`pyproject.toml` for copy_svg_translation (v2 redesign)**

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "copy-svg-translation"
version = "2.0.1"
description = "Extract translations from SVG files and inject them into others"
readme = "README.md"
requires-python = ">=3.10"
license = { text = "MIT" }
authors = [
    { name = "Your Name", email = "you@example.com" },
]
keywords = [
    "svg",
    "translation",
    "i18n",
    "l10n",
    "switch",
    "systemLanguage",
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Topic :: Software Development :: Internationalization",
    "Topic :: Software Development :: Localization",
    "Topic :: Text Processing :: Markup :: XML",
    "Typing :: Typed",
]
dependencies = [
    "lxml>=4.9",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4",
    "pytest-cov>=4.1",
    "ruff>=0.4",
    "mypy>=1.8",
    "types-lxml>=2024.4",
]
# Optional: enable when you add a CLI
# cli = []

[project.urls]
Homepage = "https://github.com/yourname/copy_svg_translation"
Documentation = "https://github.com/yourname/copy_svg_translation#readme"
Changelog = "https://github.com/yourname/copy_svg_translation/blob/main/CHANGELOG.md"
Repository = "https://github.com/yourname/copy_svg_translation"
Issues = "https://github.com/yourname/copy_svg_translation/issues"

# Optional CLI entry point (uncomment when ready)
# [project.scripts]
# svg-translate = "copy_svg_translation.cli:main"

[tool.setuptools]
include-package-data = true

[tool.setuptools.packages.find]
where = ["."]
include = ["copy_svg_translation*"]
exclude = ["tests*", "docs*"]

[tool.setuptools.package-data]
copy_svg_translation = ["py.typed"]

# ---------------------------------------------------------------------------
# Pytest
# ---------------------------------------------------------------------------
[tool.pytest.ini_options]
minversion = "7.0"
testpaths = ["tests"]
addopts = [
    "-ra",
    "--strict-markers",
    "--strict-config",
]
markers = [
    "todo: tests not yet implemented / work in progress",
    "legacy: tests for the deprecated function API",
]
filterwarnings = [
    # Surface our own deprecations during tests
    "default::DeprecationWarning:copy_svg_translation",
]

# ---------------------------------------------------------------------------
# Coverage
# ---------------------------------------------------------------------------
[tool.coverage.run]
source = ["copy_svg_translation"]
branch = true
omit = [
    "copy_svg_translation/legacy/*",
]

[tool.coverage.report]
show_missing = true
skip_covered = false
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
]

# ---------------------------------------------------------------------------
# Ruff (lint + format)
# ---------------------------------------------------------------------------
[tool.ruff]
target-version = "py310"
line-length = 100
src = ["copy_svg_translation", "tests"]

[tool.ruff.lint]
select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # pyflakes
    "I",      # isort
    "B",      # flake8-bugbear
    "UP",     # pyupgrade
    "SIM",    # flake8-simplify
    "RUF",    # ruff-specific
]
ignore = [
    "E501",   # line length handled by formatter
]

[tool.ruff.lint.isort]
known-first-party = ["copy_svg_translation"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"

# ---------------------------------------------------------------------------
# Mypy
# ---------------------------------------------------------------------------
[tool.mypy]
python_version = "3.10"
packages = ["copy_svg_translation"]
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
no_implicit_optional = true
show_error_codes = true

[[tool.mypy.overrides]]
module = ["lxml.*"]
ignore_missing_imports = true

[[tool.mypy.overrides]]
module = ["copy_svg_translation.legacy.*"]
# Legacy wrappers can be less strict while they exist
disallow_untyped_defs = false
```

---

### Companion files (minimal)

**`copy_svg_translation/py.typed`** (empty file)
Marks the package as typed for clients.

**`MANIFEST.in`** (optional if using setuptools package-data only)

```text
recursive-include copy_svg_translation *.py
include README.md
include LICENSE
include CHANGELOG.md
include pyproject.toml
```

---

### Common commands

```bash
# editable install with dev tools
pip install -e ".[dev]"

# build sdist + wheel
python -m build

# tests
pytest

# lint / format
ruff check .
ruff format .

# types
mypy copy_svg_translation
```

---

### Notes

| Setting                             | Why                                               |
| ----------------------------------- | ------------------------------------------------- |
| `name = "copy-svg-translation"`     | Conventional PyPI name (hyphens)                  |
| Import package `copy_svg_translation` | Matches your existing code layout                 |
| `requires-python = ">=3.10"`        | Fits modern typing (`X \| Y`, `slots=True`, etc.) |
| `lxml>=4.9`                         | Only hard runtime dependency                      |
| Legacy excluded from coverage       | Avoids treating temporary shims as core code      |
| `py.typed`                          | Enables type checking for downstream users        |
| Version `2.0.1`                     | Signals the class-based redesign + deprecations   |

Adjust `authors`, URLs, and license to match the real project before publishing.
