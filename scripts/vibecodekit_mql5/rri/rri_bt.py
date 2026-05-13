"""mql5-rri-bt — RRI Backtest review (5 personas × 7 dim × 8 axis).

Reads a backtest tester XML (parsed via :mod:`vibecodekit_mql5.backtest`)
plus optional Q&A answers per persona, and emits a matrix-style HTML
report.

The five personas involved at the VERIFY step (per Plan v5 §9 persona
× step matrix) are: trader, risk-auditor, broker-engineer,
strategy-architect, perf-analyst — devops is wired into the deploy step
instead.

This is a thin orchestrator: it does **not** run the backtest, it reads
artefacts already produced by `mql5-backtest` + `mql5-walkforward`.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .matrix import AXES, DIMS, MatrixReport, render_html
from .personas import PERSONA_IDS, filter_for_mode, load_persona

RRI_BT_PERSONAS: tuple[str, ...] = (
    "trader",
    "risk-auditor",
    "broker-engineer",
    "strategy-architect",
    "perf-analyst",
)

# 7 of the 8 dims are populated by backtest review; d_inference applies only
# to ONNX-bearing scaffolds and stays N/A here.
RRI_BT_DIMS: tuple[str, ...] = tuple(d for d in DIMS if d != "d_inference")


def _status_from_metrics(metrics: dict) -> dict[str, str]:
    """Map raw backtest numbers to per-dim statuses."""
    out: dict[str, str] = {}
    pf = float(metrics.get("profit_factor") or 0.0)
    sharpe = float(metrics.get("sharpe") or 0.0)
    dd_pct = float(metrics.get("max_dd_pct") or 0.0)
    trades = int(metrics.get("total_trades") or 0)

    out["d_correctness"] = "PASS" if trades > 0 else "FAIL"
    out["d_risk"] = "PASS" if dd_pct <= 30 else ("WARN" if dd_pct <= 50 else "FAIL")
    out["d_robustness"] = "PASS" if sharpe >= 0.7 else ("WARN" if sharpe >= 0.3 else "FAIL")
    out["d_perf"] = "PASS" if pf >= 1.3 else ("WARN" if pf >= 1.0 else "FAIL")
    out["d_maintainability"] = "PASS"
    out["d_observability"] = "PASS" if metrics.get("journal_lines", 0) > 0 else "WARN"
    out["d_broker_safety"] = "PASS" if metrics.get("pip_norm_log", False) else "WARN"
    return out


def review(metrics: dict, output_html: Path) -> MatrixReport:
    """Build the matrix from a metrics dict and write the HTML report."""
    statuses = _status_from_metrics(metrics)
    matrix = MatrixReport()
    for dim in RRI_BT_DIMS:
        for axis in AXES:
            status = statuses.get(dim, "N/A")
            note = ""
            if axis in ("design", "implement") and dim == "d_correctness":
                # Reviewers must sign these themselves; we surface as N/A.
                status, note = "N/A", "reviewer sign-off required"
            matrix.set(dim, axis, status, note)
    output_html.write_text(render_html(matrix), encoding="utf-8")
    return matrix


def question_count(mode: str) -> int:
    """Return the total RRI-BT question count for the chosen mode."""
    total = 0
    for pid in RRI_BT_PERSONAS:
        persona = load_persona(pid)
        total += len(filter_for_mode(persona, mode))
    return total


def main() -> int:
    ap = argparse.ArgumentParser(prog="mql5-rri-bt")
    ap.add_argument("--metrics", type=Path, required=True,
                    help="JSON file with backtest metrics")
    ap.add_argument("--mode", choices=("personal", "team", "enterprise"),
                    default="personal")
    ap.add_argument("--output", type=Path, default=Path("rri-bt.html"))
    args = ap.parse_args()

    metrics = json.loads(args.metrics.read_text(encoding="utf-8"))
    matrix = review(metrics, args.output)
    payload = {
        "personas": list(RRI_BT_PERSONAS),
        "mode": args.mode,
        "questions_to_answer": question_count(args.mode),
        "matrix_counts": matrix.counts(),
        "output": str(args.output),
    }
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
