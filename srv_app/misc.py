import sys
from pathlib import Path


def get_base_dir() -> Path:
    if getattr(sys, 'frozen', False):
        # if compiled exe
        return Path(sys.executable).resolve().parent
    # if regular .py script
    return Path(__file__).resolve().parent
