"""Vibecodekit RRI methodology package.

Exposes the legacy top-level ``mql5-rri`` ``main()`` (Step 2 template
opener) so the ``mql5-rri`` console script keeps working alongside the
per-step sub-modules (``rri.rri_bt``, ``rri.rri_rr``, ``rri.rri_chart``,
``rri.step_workflow``, ``rri.matrix``, ``rri.personas``).

The CLI implementation is duplicated in ``__main__.py`` so that
``python -m vibecodekit_mql5.rri`` resolves cleanly without triggering
the ``RuntimeWarning`` you get when ``__main__`` is imported during
package init.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parents[3] / "docs" / "rri-templates" / "step-2-rri.md.tmpl"


def render() -> str:
    if not TEMPLATE.exists():
        return f"# RRI\n\n(template not installed: {TEMPLATE})\n"
    return TEMPLATE.read_text(encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mql5-rri")
    parser.parse_args(argv)
    sys.stdout.write(render())
    return 0


__all__ = ["main", "render", "TEMPLATE"]
