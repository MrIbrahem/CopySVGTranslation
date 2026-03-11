"""Test configuration for the CopySVGTranslation test-suite."""

from __future__ import annotations

import tempfile
import pytest
import sys
import shutil
from pathlib import Path

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
