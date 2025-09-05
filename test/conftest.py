from typing import List

import pytest
from _pytest.config import Config
from _pytest.nodes import Item
from dotenv import load_dotenv

load_dotenv()

import sys
from pathlib import Path

"""
Ensure project imports work in tests without setting PYTHONPATH.
Adds both the repository root and <root>/src to sys.path.

Pytest auto-discovers conftest.py and executes it before collecting tests,
so this path tweak applies to all tests under this directory and its subfolders.
"""

THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parent          # adjust to THIS_DIR.parents[2] if needed
SRC_DIR = REPO_ROOT / "src"

for p in (REPO_ROOT, SRC_DIR):
    p_str = str(p)
    if p_str not in sys.path:
        sys.path.insert(0, p_str)

