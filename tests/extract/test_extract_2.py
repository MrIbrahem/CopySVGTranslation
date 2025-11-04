

import sys
import tempfile
import shutil
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from CopySVGTranslation import extract


# -------------------------------
# Fixtures
# -------------------------------

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test use."""
    d = Path(tempfile.mkdtemp())
    yield d
    shutil.rmtree(d)


class TestExtractor:
    """Test cases for extraction functions."""

    def test_extract_with_no_tspan_ids(self, temp_dir):
        """Test extraction with multiple languages."""
        svg = temp_dir / "test.svg"
        svg.write_text(
            '''<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg">
            <switch>
                <text id="t0-ar" systemLanguage="ar">
                    <tspan>مرحبا</tspan>
                </text>
                <text id="t0-fr" systemLanguage="fr">
                    <tspan>Bonjour</tspan>
                </text>
                <text id="t0">
                    <tspan>Hello</tspan>
                </text>
            </switch>
            </svg>''',
            encoding='utf-8',
        )
        result = extract(svg)
        assert result is not None
        assert "new" in result
        # assert "ar" in result["new"]["hello"]
        # assert "fr" in result["new"]["hello"]

    def test_extract_with_span_and_text_ids(self, temp_dir):
        """Test extraction with multiple languages."""
        svg = temp_dir / "test.svg"
        svg.write_text(
            '''<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg">
            <switch>
                <text id="t0-ar" systemLanguage="ar">
                    <tspan id="t0-ar">مرحبا</tspan>
                </text>
                <text id="t0-fr" systemLanguage="fr">
                    <tspan id="t0-fr" >Bonjour</tspan>
                </text>
                <text id="t0">
                    <tspan id="t0">Hello</tspan>
                </text>
            </switch>
            </svg>''',
            encoding='utf-8',
        )
        result = extract(svg)
        print(result)
        assert result is not None
        assert "new" in result
        assert "ar" in result["new"]["hello"]
        assert "fr" in result["new"]["hello"]
