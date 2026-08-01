"""
python I:/TOOLFORGE_TOOLS/SVG_PY/CopySVGTranslation/tests/manually/extract.py
"""

import logging
import tempfile
from pathlib import Path

from CopySVGTranslation import extract
from CopySVGTranslation.injection import make_translation_ready

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console = logging.StreamHandler()
console.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
logger.addHandler(console)

temp_dir = Path(tempfile.mkdtemp())
svg_file = temp_dir / "test.svg"

svg_file.write_text(
    """<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg">
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
    </svg>""",
    encoding="utf-8",
)

make_translation_ready(svg_file, write_back=True)

result = extract(svg_file)

print(result)
