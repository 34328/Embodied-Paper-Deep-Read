#!/usr/bin/env python3
"""Locate an interpreter that can import PyMuPDF, so `python3 script.py` just works.

`install.sh` falls back to a private virtualenv at `<skill-dir>/.venv` when the system
interpreter is externally managed (PEP 668). The documented commands still say
`python3 <skill-dir>/scripts/...`, so the scripts re-exec themselves into that venv
instead of asking the caller to remember a second interpreter path.
"""

import os
import sys

REEXEC_GUARD = "EPDR_PYMUPDF_REEXEC"

HINT = """PyMuPDF is not available for this interpreter:
  {exe}
Install the dependencies with the repository installer:
  bash install.sh
or install it directly for this interpreter:
  {exe} -m pip install 'PyMuPDF>=1.23,<2'"""


def venv_python():
    """Return the skill's private venv interpreter, or None when it does not exist."""
    skill_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if os.name == "nt":
        candidate = os.path.join(skill_dir, ".venv", "Scripts", "python.exe")
    else:
        candidate = os.path.join(skill_dir, ".venv", "bin", "python3")
    if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
        return candidate
    return None


def ensure_pymupdf():
    """Import PyMuPDF, re-executing into the skill's own venv when the current one lacks it."""
    try:
        import fitz  # noqa: F401
        return
    except ImportError:
        pass

    candidate = venv_python()
    same = candidate and os.path.realpath(candidate) == os.path.realpath(sys.executable)
    if candidate and not same and not os.environ.get(REEXEC_GUARD):
        os.environ[REEXEC_GUARD] = "1"
        script = os.path.abspath(sys.argv[0])
        os.execv(candidate, [candidate, script] + sys.argv[1:])

    sys.exit(HINT.format(exe=sys.executable))
