"""

"""
import os
from pathlib import Path
# ---
from dotenv import load_dotenv
# ---
HOME = os.getenv("HOME")
# ---
load_dotenv()
# ---
home_dir = HOME if HOME else os.path.expanduser("~")
# ---
SVG_DATA_PATH = os.getenv("SVG_DATA_PATH", f"{home_dir}/svg_data")
LOG_DIR_PATH = os.getenv("LOG_PATH", f"{home_dir}/logs")

svg_data_dir = Path(SVG_DATA_PATH)
svg_data_dir.mkdir(parents=True, exist_ok=True)

