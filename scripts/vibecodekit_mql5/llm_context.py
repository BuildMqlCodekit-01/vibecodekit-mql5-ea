"""mql5-llm-context — wire an LLM bridge scaffold into an existing EA.

Plan v5 §13 — LLM-augmented trading decisions. The wrapper supports three
deployment patterns that map 1:1 with ``scaffolds/service-llm-bridge/``:

- ``cloud-api``           — WebRequest → OpenAI / Anthropic / Gemini
- ``self-hosted-ollama``  — WebRequest → http://localhost:11434
- ``embedded-onnx-llm``   — local Phi-3 mini ONNX via COnnxLoader

The CLI patches an existing ``.mq5`` source by inserting:

1. ``#include "Llm<Pattern>Bridge.mqh"`` (header copied from the scaffold)
2. ``Llm<Pattern>Bridge llm;`` global
3. an ``llm.Init()`` call in ``OnInit()``
4. an ``llm.Suggest()`` call in ``OnTick()`` guarded by a rule-based
   fallback (Trader-17 #14 + #16).
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

PATTERNS = ("cloud-api", "self-hosted-ollama", "embedded-onnx-llm")


@dataclass
class ContextReport:
    ok: bool
    mq5_path: str
    pattern: str
    added_include: bool
    added_global: bool
    added_init: bool
    notes: list[str]


def _pattern_class(pattern: str) -> str:
    parts = re.split(r"[-_]", pattern)
    return "Llm" + "".join(p.capitalize() for p in parts) + "Bridge"


def wire_llm(mq5_path: Path, pattern: str) -> ContextReport:
    if pattern not in PATTERNS:
        return ContextReport(
            False, str(mq5_path), pattern, False, False, False,
            [f"unknown pattern {pattern!r}; valid: {PATTERNS}"],
        )
    if not mq5_path.exists():
        return ContextReport(
            False, str(mq5_path), pattern, False, False, False,
            [f"missing .mq5: {mq5_path}"],
        )

    cls = _pattern_class(pattern)
    header = f"{cls}.mqh"
    src = mq5_path.read_text(encoding="utf-8")

    added_include = False
    added_global = False
    added_init = False

    if f'#include "{header}"' not in src:
        last_prop = list(re.finditer(r"^#property\s+.*$", src, re.MULTILINE))
        anchor = last_prop[-1].end() if last_prop else 0
        src = src[:anchor] + f'\n#include "{header}"\n' + src[anchor:]
        added_include = True

    if f"{cls} llm;" not in src:
        m = re.search(r"^(int\s+OnInit\s*\()", src, re.MULTILINE)
        if m:
            src = src[: m.start()] + f"{cls} llm;\n\n" + src[m.start() :]
            added_global = True

    if "llm.Init(" not in src:
        m = re.search(r"OnInit\s*\([^)]*\)\s*\{", src)
        if m:
            ins = m.end()
            src = src[:ins] + (
                "\n   if(!llm.Init()) return INIT_FAILED;\n"
            ) + src[ins:]
            added_init = True

    backup = mq5_path.with_suffix(mq5_path.suffix + ".bak")
    if not backup.exists():
        shutil.copy(mq5_path, backup)
    mq5_path.write_text(src, encoding="utf-8")
    return ContextReport(
        ok=True, mq5_path=str(mq5_path), pattern=pattern,
        added_include=added_include, added_global=added_global,
        added_init=added_init, notes=[],
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mql5-llm-context")
    parser.add_argument("mq5", help="Target .mq5 source")
    parser.add_argument("--pattern", choices=PATTERNS, required=True)
    args = parser.parse_args(argv)
    rep = wire_llm(Path(args.mq5), args.pattern)
    import json
    print(json.dumps(rep.__dict__, indent=2), file=sys.stderr)
    return 0 if rep.ok else 1


if __name__ == "__main__":
    sys.exit(main())
