"""mql5-review — generic review wrapper that opens the appropriate template
+ invokes a chosen RRI persona to drive the conversation.

This command is *intentionally* a thin shell:

  - pick a step template (default: ``step-7-verify.md.tmpl``)
  - pick a persona (default: ``trader``)
  - print the persona description, the active-mode questions, and the
    template body — that combined output is what the reviewer answers.

It writes the rendered combo to ``--output`` (default ``review.md``) so
the reviewer can keep editing it inline. No external services involved.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ..rri.personas import PERSONA_IDS, filter_for_mode, load_persona
from ..rri.step_workflow import STEPS, render_template


def render(persona_id: str, step: str, mode: str) -> str:
    persona = load_persona(persona_id)
    questions = filter_for_mode(persona, mode)
    header = (
        f"# Review — persona: {persona.persona} / step: {step} / mode: {mode}\n\n"
        f"_{persona.description}_\n\n"
        "## Questions\n\n"
    )
    q_lines = "\n".join(
        f"- [ ] **{q.id}** ({q.priority}) — {q.text}" for q in questions
    )
    body = render_template(step)
    return header + q_lines + "\n\n## Step template\n\n" + body


def main() -> int:
    ap = argparse.ArgumentParser(prog="mql5-review")
    ap.add_argument("--persona", choices=PERSONA_IDS, default="trader")
    ap.add_argument("--step", choices=STEPS, default="verify")
    ap.add_argument("--mode", choices=("personal", "team", "enterprise"),
                    default="personal")
    ap.add_argument("--output", type=Path, default=Path("review.md"))
    args = ap.parse_args()

    body = render(args.persona, args.step, args.mode)
    args.output.write_text(body, encoding="utf-8")
    print(json.dumps({
        "persona": args.persona,
        "step": args.step,
        "mode": args.mode,
        "output": str(args.output),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
