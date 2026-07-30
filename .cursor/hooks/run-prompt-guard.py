#!/usr/bin/env python3
"""Portable Cursor hook runner for Prompt Guard.

Works when the package is installed (`pip install -e .`) or when this repo
is checked out locally (adds the repo root to sys.path automatically).
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from prompt_guard.hook import main

if __name__ == "__main__":
    raise SystemExit(main())
