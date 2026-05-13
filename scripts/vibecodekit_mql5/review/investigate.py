"""mql5-investigate — open-ended investigation review.

When a backtest, walkforward, or live deployment misbehaves, the
"investigate" review aims to capture *what we don't yet understand*.
It bundles perf-analyst + strategy-architect + the SCAN step template
into a single document so the reviewer can record hypotheses and the
data each one needs.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ..rri.personas import filter_for_mode, load_persona
from ..rri.step_workflow import render_template

PERSONAS: tuple[str, ...] = ("perf-analyst", "strategy-architect")
DEFAULT_STEPS: tuple[str, ...] = ("scan", "rri")


def render(mode: str, steps: tuple[str, ...] = DEFAULT_STEPS) -> str:
    out: list[str] = ["# Investigation review", "",
                      "_Goal: capture hypotheses + the evidence each needs._", ""]
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
    out.append("## Hypotheses\n\n- [ ] Hypothesis 1: ...\n- [ ] Hypothesis 2: ...\n")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(prog="mql5-investigate")
    ap.add_argument("--mode", choices=("personal", "team", "enterprise"),
                    default="personal")
    ap.add_argument("--output", type=Path, default=Path("investigate.md"))
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
