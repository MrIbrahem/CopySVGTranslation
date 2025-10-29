"""Additional comprehensive pytest tests for CopySvgTranslate."""

import json
import sys
import tempfile
from pathlib import Path
from lxml import etree
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from CopySvgTranslate import match_nested_tags, fix_nested_file
