"""mql5-rri-chart — optional RRI review for indicator development.

Indicator-only EAs / pure-MQL5 indicators don't go through the same
risk-auditor / broker-engineer lens that order-placing EAs do, so this
command runs a slimmed-down review covering correctness, observability,
and perf only. Personas involved: trader (UX) + perf-analyst.

This command is *optional* — it's only invoked from the indicator-only
scaffold (Phase D) and is treated as a sanity check, not a gate.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .matrix import AXES, MatrixReport, render_html
from .personas import filter_for_mode, load_persona

RRI_CHART_PERSONAS: tuple[str, ...] = ("trader", "perf-analyst")
RRI_CHART_DIMS: tuple[str, ...] = ("d_correctness", "d_observability", "d_perf")


def review(metrics: dict, output_html: Path) -> MatrixReport:
    matrix = MatrixReport()
    correctness = "PASS" if metrics.get("compile_errors", 1) == 0 else "FAIL"
    observability = "PASS" if metrics.get("journal_lines", 0) > 0 else "WARN"
    perf = "PASS" if metrics.get("ontick_latency_us", 9999) < 1000 else "WARN"
    status_for = {
        "d_correctness": correctness,
        "d_observability": observability,
        "d_perf": perf,
    }
    for dim in RRI_CHART_DIMS:
        for axis in AXES:
            matrix.set(dim, axis, status_for[dim])
    output_html.write_text(render_html(matrix), encoding="utf-8")
    return matrix


def question_count(mode: str) -> int:
    return sum(
        len(filter_for_mode(load_persona(pid), mode)) for pid in RRI_CHART_PERSONAS
    )


def main() -> int:
    ap = argparse.ArgumentParser(prog="mql5-rri-chart")
    ap.add_argument("--metrics", type=Path, required=True)
    ap.add_argument("--mode", choices=("personal", "team", "enterprise"),
                    default="personal")
    ap.add_argument("--output", type=Path, default=Path("rri-chart.html"))
    args = ap.parse_args()

    metrics = json.loads(args.metrics.read_text(encoding="utf-8"))
    matrix = review(metrics, args.output)
    print(json.dumps({
        "personas": list(RRI_CHART_PERSONAS),
        "mode": args.mode,
        "questions_to_answer": question_count(args.mode),
        "matrix_counts": matrix.counts(),
        "output": str(args.output),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
