# Development Guide

> **Relevant source files**
> * [.github/workflows/pytest.yaml](https://github.com/MrIbrahem/CopySVGTranslation/blob/d984a401/.github/workflows/pytest.yaml)
> * [.github/workflows/python-publish.yml](https://github.com/MrIbrahem/CopySVGTranslation/blob/d984a401/.github/workflows/python-publish.yml)
> * [.gitignore](https://github.com/MrIbrahem/CopySVGTranslation/blob/d984a401/.gitignore)
> * [dev-requirements.txt](https://github.com/MrIbrahem/CopySVGTranslation/blob/d984a401/dev-requirements.txt)
> * [pyproject.toml](https://github.com/MrIbrahem/CopySVGTranslation/blob/d984a401/pyproject.toml)
> * [pytest.ini](https://github.com/MrIbrahem/CopySVGTranslation/blob/d984a401/pytest.ini)

This document provides essential information for developers contributing to the CopySVGTranslation codebase. It covers project structure, testing procedures, building and publishing workflows, CI/CD automation, and code quality tools.

For information about using the package as an end user, see [Getting Started](/MrIbrahem/CopySVGTranslation/2-getting-started). For API documentation, see [API Reference](/MrIbrahem/CopySVGTranslation/6-api-reference).

## Overview

The CopySVGTranslation project is structured as a modern Python package using `pyproject.toml` for configuration, `hatchling` as the build backend, and GitHub Actions for CI/CD automation. The package requires Python 3.11+ and has minimal runtime dependencies.

**Development Stack:**

| Component | Tool | Version Requirement |
| --- | --- | --- |
| Build Backend | Hatchling | >=1.17 |
| Testing Framework | pytest | (latest) |
| XML Processing | lxml | >=4.9 |
| Code Formatter | black / ruff | line-length=120 |
| Type Checker | mypy / pyright | Python 3.13 |
| CI/CD | GitHub Actions | - |

Sources: [pyproject.toml L1-L13](https://github.com/MrIbrahem/CopySVGTranslation/blob/d984a401/pyproject.toml#L1-L13)

 [pyproject.toml L27-L28](https://github.com/MrIbrahem/CopySVGTranslation/blob/d984a401/pyproject.toml#L27-L28)

 [pyproject.toml L197-L215](https://github.com/MrIbrahem/CopySVGTranslation/blob/d984a401/pyproject.toml#L197-L215)

## Project Structure

For a detailed breakdown of the directory layout and module organization, see **[Project Structure](/MrIbrahem/CopySVGTranslation/7.1-project-structure)**.

### Directory Layout

```go
CopySVGTranslation/
├── CopySVGTranslation/           # Main package directory
│   ├── extraction/              # SVG → JSON extraction logic
│   ├── injection/               # JSON → SVG injection logic
│   ├── nested_analyze/          # Nested element detection and fixing
│   ├── text_utils.py            # Text normalization utilities
│   ├── titles.py                # Title translation handling
│   └── workflows.py             # High-level combined workflows
├── tests/                        # Test suite mirroring package structure
├── .github/workflows/            # CI/CD automation (pytest, publish)
├── pyproject.toml               # Unified tool configuration
├── dev-requirements.txt         # Development/Test dependencies
├── pytest.ini                   # pytest configuration
└── .gitignore                   # Version control exclusions
```

### Module Architecture

```mermaid
flowchart TD

INIT["init.py<br>Public API Facade"]
EXTRACTOR["extractor.py<br>extract()"]
INJECTOR["injector.py<br>inject()"]
PREP["preparation.py<br>make_translation_ready()"]
BATCH["batch.py<br>start_injects()"]
NEST_NEW["find_nested_new.py<br>fix_nested_tspans()"]
TEXT["text_utils.py<br>normalize_text()"]
TITLES["titles.py<br>make_title_translations()"]
WORKFLOWS["workflows.py<br>svg_extract_and_inject()"]

INIT --> EXTRACTOR
INIT --> INJECTOR
INIT --> PREP
INIT --> BATCH
INIT --> NEST_NEW
INIT --> TEXT
INIT --> TITLES
INIT --> WORKFLOWS

subgraph Utilities ["Utilities"]
    TEXT
    TITLES
    WORKFLOWS
end

subgraph Nested_Analyze[nested_analyze/] ["Nested_Analyze[nested_analyze/]"]
    NEST_NEW
end

subgraph Injection_Module[injection/] ["Injection_Module[injection/]"]
    INJECTOR
    PREP
    BATCH
end

subgraph Extraction_Module[extraction/] ["Extraction_Module[extraction/]"]
    EXTRACTOR
end

subgraph Package_Root[CopySVGTranslation/] ["Package_Root[CopySVGTranslation/]"]
    INIT
end
```

**Module Organization Diagram: The package structure uses `__init__.py` to expose core functionality from specialized submodules.**

Sources: [pyproject.toml L20-L21](https://github.com/MrIbrahem/CopySVGTranslation/blob/d984a401/pyproject.toml#L20-L21)

 [pyproject.toml L218](https://github.com/MrIbrahem/CopySVGTranslation/blob/d984a401/pyproject.toml#L218-L218)

## Testing

The test suite is built on `pytest` and covers unit, integration, and workflow testing. For detailed information on test categories and coverage, see **[Testing](/MrIbrahem/CopySVGTranslation/7.2-testing)**.

### Running Tests

To run the complete test suite:

```
pytest
```

The configuration in `pytest.ini` ensures that tests are discovered in the `tests` directory and follows naming conventions like `test*.py`.

Sources: [pytest.ini L1-L5](https://github.com/MrIbrahem/CopySVGTranslation/blob/d984a401/pytest.ini#L1-L5)

 [dev-requirements.txt L1-L2](https://github.com/MrIbrahem/CopySVGTranslation/blob/d984a401/dev-requirements.txt#L1-L2)

## Building and Publishing

The project uses `hatchling` to build standard Python distributions. For the full process including PyPI publishing, see **[Building and Publishing](/MrIbrahem/CopySVGTranslation/7.3-building-and-publishing)**.

### Build Configuration

The build system is defined in `pyproject.toml`:

| Configuration | Value |
| --- | --- |
| `build-backend` | `hatchling.build` |
| `name` | `CopySVGTranslation` |
| `version` | `0.2.7` |
| `requires-python` | `>=3.11` |

Sources: [pyproject.toml L1-L10](https://github.com/MrIbrahem/CopySVGTranslation/blob/d984a401/pyproject.toml#L1-L10)

## CI/CD Workflows

Automated workflows handle code validation and package delivery. For details on specific GitHub Actions, see **[CI/CD Workflows](/MrIbrahem/CopySVGTranslation/7.4-cicd-workflows)**.

```mermaid
flowchart TD

RELEASE["GitHub Release"]
BUILD["Build Dist<br>(python -m build)"]
PUBLISH["Publish to PyPI<br>(Trusted Publishing)"]
PR["Pull Request"]
RUN_TESTS["Run pytest<br>(Python 3.10)"]

subgraph CD_Pipeline[python-publish.yml] ["CD_Pipeline[python-publish.yml]"]
    RELEASE
    BUILD
    PUBLISH
    RELEASE --> BUILD
    BUILD --> PUBLISH
end

subgraph CI_Pipeline[pytest.yaml] ["CI_Pipeline[pytest.yaml]"]
    PR
    RUN_TESTS
    PR --> RUN_TESTS
end
```

**Workflow Overview: Automated testing on PRs and automated PyPI deployment on releases.**

Sources: [.github/workflows/pytest.yaml L1-L34](https://github.com/MrIbrahem/CopySVGTranslation/blob/d984a401/.github/workflows/pytest.yaml#L1-L34)

 [.github/workflows/python-publish.yml L1-L62](https://github.com/MrIbrahem/CopySVGTranslation/blob/d984a401/.github/workflows/python-publish.yml#L1-L62)

## Code Quality Tools

The project enforces strict coding standards using a variety of linters and formatters. For configuration details for each tool, see **[Code Quality Tools](/MrIbrahem/CopySVGTranslation/7.5-code-quality-tools)**.

| Tool | Purpose | Configuration |
| --- | --- | --- |
| **Black** | Formatting | `line-length = 120` |
| **Ruff** | Linting & Fixes | Extensive rule selection (E, F, W, B, I, N, UP) |
| **Mypy** | Type Checking | `python_version = 3.13` |
| **Isort** | Import Sorting | `profile = "black"` |

Sources: [pyproject.toml L26-L28](https://github.com/MrIbrahem/CopySVGTranslation/blob/d984a401/pyproject.toml#L26-L28)

 [pyproject.toml L49-L51](https://github.com/MrIbrahem/CopySVGTranslation/blob/d984a401/pyproject.toml#L49-L51)

 [pyproject.toml L79-L188](https://github.com/MrIbrahem/CopySVGTranslation/blob/d984a401/pyproject.toml#L79-L188)

 [pyproject.toml L196-L197](https://github.com/MrIbrahem/CopySVGTranslation/blob/d984a401/pyproject.toml#L196-L197)