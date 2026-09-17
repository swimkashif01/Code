"""Pytest configuration for the expense tracker test suite.

Ensures ``core/`` is importable as ``expense_tracker`` regardless of the
directory pytest is invoked from.
"""

import os
import sys

_CORE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "core")
_CORE_DIR = os.path.normpath(_CORE_DIR)

if _CORE_DIR not in sys.path:
    sys.path.insert(0, _CORE_DIR)
