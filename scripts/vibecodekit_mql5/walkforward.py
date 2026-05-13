"""mql5-walkforward — Forward 1/4 (75% IS, 25% OOS) orchestrator.

Drives two `backtest.parse_xml_report` runs (one IS-only XML, one OOS-only
XML) and computes the IS/OOS Sharpe correlation. Acceptance:

    ratio >= 0.5   → PASS
    0.3 <= ratio < 0.5 → WARN
    ratio < 0.3   → FAIL

CLI:
    python -m vibecodekit_mql5.walkforward <is.xml> <oos.xml>

Exit codes:
    0 — PASS or WARN
    1 — FAIL (ratio < 0.3 OR missing Sharpe)
    2 — invocation error
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

from vibecodekit_mql5.backtest import (
    BacktestResult,
    parse_xml_report_file,
)


@dataclass
class WalkforwardResult:
    is_sharpe: float
    oos_sharpe: float
    correlation: float
    verdict: str  # "PASS" | "WARN" | "FAIL"

    def to_dict(self) -> dict:
        return {
            "is_sharpe": self.is_sharpe,
            "oos_sharpe": self.oos_sharpe,
            "correlation": round(self.correlation, 4),
            "verdict": self.verdict,
        }


PASS_THRESHOLD = 0.5
WARN_THRESHOLD = 0.3


def correlation(is_sharpe: float, oos_sharpe: float) -> float:
    """OOS/IS ratio, clamped to [0,1]; 0 when IS is zero or negative."""
    if is_sharpe <= 0:
        return 0.0
    return max(0.0, min(1.0, oos_sharpe / is_sharpe))


def verdict(corr: float) -> str:
    if corr >= PASS_THRESHOLD:
        return "PASS"
    if corr >= WARN_THRESHOLD:
        return "WARN"
    return "FAIL"


def evaluate(is_report: BacktestResult, oos_report: BacktestResult) -> WalkforwardResult:
    corr = correlation(is_report.sharpe, oos_report.sharpe)
    return WalkforwardResult(
        is_sharpe=is_report.sharpe,
        oos_sharpe=oos_report.sharpe,
        correlation=corr,
        verdict=verdict(corr),
    )


# Forward modes in MT5 tester.ini:
#   0  = no forward
#   1  = Forward 1/2 (50% IS, 50% OOS)
#   2  = Forward 1/3 (66% IS, 33% OOS)
#   3  = Forward 1/4 (75% IS, 25% OOS)   ← Plan v5 default
#   4  = Custom
FORWARD_QUARTER = 3


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="mql5-walkforward", description=__doc__.splitlines()[0])
    p.add_argument("is_xml", help="In-sample tester report XML")
    p.add_argument("oos_xml", help="Out-of-sample tester report XML")
    args = p.parse_args(argv)

    try:
        is_r = parse_xml_report_file(Path(args.is_xml))
        oos_r = parse_xml_report_file(Path(args.oos_xml))
    except FileNotFoundError as e:
        print(f"[walkforward] missing report: {e}", file=sys.stderr)
        return 2

    result = evaluate(is_r, oos_r)
    print(json.dumps(result.to_dict(), indent=2))
    return 0 if result.verdict in ("PASS", "WARN") else 1


if __name__ == "__main__":
    sys.exit(main())
