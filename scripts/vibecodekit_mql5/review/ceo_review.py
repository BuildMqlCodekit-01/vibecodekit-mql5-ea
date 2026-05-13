"""mql5-ceo-review — executive review (trader + strategy-architect).

Frames the EA in business / strategy terms: are we shipping something
the trader wants, and does the strategy edge actually exist? Bias
toward VISION + REFINE steps.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ..rri.personas import filter_for_mode, load_persona
from ..rri.step_workflow import render_template

PERSONAS: tuple[str, ...] = ("trader", "strategy-architect")
DEFAULT_STEPS: tuple[str, ...] = ("vision", "refine")


def render(mode: str, steps: tuple[str, ...] = DEFAULT_STEPS) -> str:
    out: list[str] = ["# CEO review", ""]
    for pid in PERSONAS:
        persona = load_persona(pid)
        out.append(f"## Persona: {persona.persona}")
        out.append(f"_{persona.description}_\n")
        for q in filter_for_mode(persona, mode):
            out.append(f"- [ ] **{q.id}** ({q.priority}) — {q.text}")
        out.append("")
    out.append("## Step templates\n")
    for step in steps:
        out.append(f"### {step}\n")
        out.append(render_template(step))
        out.append("")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(prog="mql5-ceo-review")
    ap.add_argument("--mode", choices=("personal", "team", "enterprise"),
                    default="personal")
    ap.add_argument("--output", type=Path, default=Path("ceo-review.md"))
    args = ap.parse_args()
    args.output.write_text(render(args.mode), encoding="utf-8")
    print(json.dumps({
        "personas": list(PERSONAS),
        "mode": args.mode,
        "output": str(args.output),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
