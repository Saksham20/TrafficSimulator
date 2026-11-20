"""Picks which corridor's inputs file to use.

    CORRIDOR=silk_board  python model.py     (default)
    CORRIDOR=mysore_road python model.py
"""

import importlib
import os

NAME = os.environ.get("CORRIDOR", "silk_board")
I = importlib.import_module(f"inputs_{NAME}")
OUT = f"outputs/{NAME}"
os.makedirs(OUT, exist_ok=True)
