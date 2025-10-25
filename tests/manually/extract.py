"""
python I:/SVG_PY/CopySvgTranslate/tests/manually/extract.py
"""
import sys
import tempfile
import logging
from pathlib import Path

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
logger.addHandler(console_handler)

console_handler.setLevel(logging.INFO)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from CopySvgTranslate import extract

temp_dir = Path(tempfile.mkdtemp())
svg_file = temp_dir / "test.svg"

svg_file.write_text(
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

result = extract(svg_file)

print(result)
