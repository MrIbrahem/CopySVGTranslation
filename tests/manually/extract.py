"""
python I:/SVG_PY/CopySVGTranslation/tests/manually/extract.py
"""
import sys
import tempfile
import logging
from pathlib import Path

logger = logging.getLogger("CopySVGTranslation")
logger.setLevel(logging.DEBUG)

console = logging.StreamHandler()
console.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
logger.addHandler(console)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from CopySVGTranslation import extract, make_translation_ready

temp_dir = Path(tempfile.mkdtemp())
svg_file = temp_dir / "test.svg"

svg_file.write_text(
    '''<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg">
    <switch>
        <text id="t0-ar" systemLanguage="ar">
            <tspan id="t0-ar">الموسيقى في عام 2020</tspan>
        </text>
        <text id="t0-fr" systemLanguage="fr">
            <tspan id="t0-fr">La musique en 2020</tspan>
        </text>
        <text id="t0">
            <tspan id="t0">Music in 2020</tspan>
        </text>
    </switch>
    <switch>
        <text id="t0-ar" systemLanguage="ar">
            <tspan id="t0-ar">مرحبا</tspan>
        </text>
        <text id="t0-fr" systemLanguage="fr">
            <tspan id="t0-fr">Bonjour</tspan>
        </text>
        <text id="t0">
            <tspan id="t0">Hello</tspan>
        </text>
    </switch>
    </svg>''',
    encoding='utf-8',
)

make_translation_ready(svg_file, write_back=True)

result = extract(svg_file)

print(result)
