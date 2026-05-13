"""mql5-cso — Chief Safety Officer review (risk-auditor lens).

A single-persona drill on the risk envelope. Bias toward RRI + VERIFY
steps. Useful for compliance sign-off before live deployment.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ..rri.personas import filter_for_mode, load_persona
from ..rri.step_workflow import render_template

PERSONA: str = "risk-auditor"
DEFAULT_STEPS: tuple[str, ...] = ("rri", "verify")


def render(mode: str, steps: tuple[str, ...] = DEFAULT_STEPS) -> str:
    persona = load_persona(PERSONA)
    out: list[str] = ["# Chief Safety Officer review", ""]
    out.append(f"## Persona: {persona.persona}")
    out.append(f"_{persona.description}_\n")
    for q in filter_for_mode(persona, mode):
        out.append(f"- [ ] **{q.id}** ({q.priority}) — {q.text}")
    out.append("\n## Step templates\n")
    for step in steps:
        out.append(f"### {step}\n")
        out.append(render_template(step))
        out.append("")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(prog="mql5-cso")
    ap.add_argument("--mode", choices=("personal", "team", "enterprise"),
                    default="personal")
    ap.add_argument("--output", type=Path, default=Path("cso-review.md"))
    args = ap.parse_args()
    args.output.write_text(render(args.mode), encoding="utf-8")
    print(json.dumps({
        "persona": PERSONA,
        "mode": args.mode,
        "output": str(args.output),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
