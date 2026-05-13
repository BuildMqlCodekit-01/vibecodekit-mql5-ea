"""mql5-overfit-check — OOS/IS Sharpe ratio sanity gate.

Reads two XML reports (in-sample + out-of-sample) and computes the ratio
of OOS-Sharpe to IS-Sharpe. Per Plan v5 §12:

    ratio >= 0.7   → PASS  (OOS holds at least 70% of IS quality)
    0.5 <= ratio < 0.7 → WARN
    ratio < 0.5   → FAIL  (suspected overfitted)

CLI:
    python -m vibecodekit_mql5.overfit_check <is.xml> <oos.xml>

Exit codes:
    0 — PASS or WARN
    1 — FAIL
    2 — invocation error
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

from vibecodekit_mql5.backtest import parse_xml_report_file


PASS_THRESHOLD = 0.7
WARN_THRESHOLD = 0.5


@dataclass
class OverfitResult:
    is_sharpe: float
    oos_sharpe: float
    ratio: float
    verdict: str

    def to_dict(self) -> dict:
        return {
            "is_sharpe": self.is_sharpe,
            "oos_sharpe": self.oos_sharpe,
            "ratio": round(self.ratio, 4),
            "verdict": self.verdict,
        }


def ratio(is_sharpe: float, oos_sharpe: float) -> float:
    if is_sharpe <= 0:
        return 0.0
    return oos_sharpe / is_sharpe


def verdict(r: float) -> str:
    if r >= PASS_THRESHOLD:
        return "PASS"
    if r >= WARN_THRESHOLD:
        return "WARN"
    return "FAIL"


def evaluate(is_sharpe: float, oos_sharpe: float) -> OverfitResult:
    r = ratio(is_sharpe, oos_sharpe)
    return OverfitResult(is_sharpe=is_sharpe, oos_sharpe=oos_sharpe,
                         ratio=r, verdict=verdict(r))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="mql5-overfit-check", description=__doc__.splitlines()[0])
    p.add_argument("is_xml")
    p.add_argument("oos_xml")
    args = p.parse_args(argv)

    try:
        is_r = parse_xml_report_file(Path(args.is_xml))
        oos_r = parse_xml_report_file(Path(args.oos_xml))
    except FileNotFoundError as e:
        print(f"[overfit_check] missing report: {e}", file=sys.stderr)
        return 2

    result = evaluate(is_r.sharpe, oos_r.sharpe)
    print(json.dumps(result.to_dict(), indent=2))
    return 0 if result.verdict in ("PASS", "WARN") else 1


if __name__ == "__main__":
    sys.exit(main())
