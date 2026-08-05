"""Test configuration for the CopySVGTranslation test-suite."""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

import pytest

# Ensure the project root (which contains the ``CopySVGTranslation`` package) is importable
PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test use."""
    d = Path(tempfile.mkdtemp())
    yield d
    shutil.rmtree(d)


@pytest.fixture
def fixtures_dir():
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def tests_files_dir():
    return Path(__file__).parent / "tests_files"
