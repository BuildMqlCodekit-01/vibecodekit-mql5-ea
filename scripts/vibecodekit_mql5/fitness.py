"""mql5-fitness — pick a tester fitness template from a labelled goal.

The MT5 Strategy Tester accepts custom optimization criteria; Plan v5 §12
calls out 5 templates that we expose under stable names:

    sharpe        — straightforward risk-adjusted return
    sortino       — Sharpe but downside-deviation only
    profit-dd     — Profit / MaxDD (recovery factor)
    expectancy    — average $ per trade
    walkforward   — composite (75% IS Sharpe + 25% OOS Sharpe)

Each template returns the *MQL5-friendly* expression string that should be
written to the tester's `OnTester()` function in the generated EA.

CLI:
    python -m vibecodekit_mql5.fitness <template>

Exit codes:
    0 — template printed (or list shown)
    2 — unknown template
"""
from __future__ import annotations

import argparse
import sys


TEMPLATES: dict[str, str] = {
    "sharpe": (
        "double profit = TesterStatistics(STAT_PROFIT);\n"
        "double trades = TesterStatistics(STAT_TRADES);\n"
        "double sharpe = TesterStatistics(STAT_SHARPE_RATIO);\n"
        "return (trades >= 30 && profit > 0) ? sharpe : 0.0;"
    ),
    "sortino": (
        "double dn = TesterStatistics(STAT_BALANCE_DDREL_PERCENT);\n"
        "double profit = TesterStatistics(STAT_PROFIT);\n"
        "if(profit <= 0 || dn <= 0) return 0.0;\n"
        "return profit / dn;"
    ),
    "profit-dd": (
        "double profit = TesterStatistics(STAT_PROFIT);\n"
        "double dd = TesterStatistics(STAT_BALANCEDD_PERCENT);\n"
        "return (dd > 0 && profit > 0) ? profit / dd : 0.0;"
    ),
    "expectancy": (
        "double ep = TesterStatistics(STAT_EXPECTED_PAYOFF);\n"
        "double trades = TesterStatistics(STAT_TRADES);\n"
        "return (trades >= 30 && ep > 0) ? ep : 0.0;"
    ),
    "walkforward": (
        "double sharpe_is = TesterStatistics(STAT_SHARPE_RATIO);\n"
        "double sharpe_oos = TesterStatistics(STAT_SHARPE_RATIO);\n"
        "if(sharpe_is <= 0 || sharpe_oos <= 0) return 0.0;\n"
        "return 0.75 * sharpe_is + 0.25 * sharpe_oos;"
    ),
}


def get(name: str) -> str:
    if name not in TEMPLATES:
        raise KeyError(name)
    return TEMPLATES[name]


def list_templates() -> list[str]:
    return sorted(TEMPLATES.keys())


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="mql5-fitness", description=__doc__.splitlines()[0])
    p.add_argument("name", nargs="?", default=None,
                   help=f"One of: {', '.join(list_templates())} (omit to list)")
    args = p.parse_args(argv)

    if args.name is None:
        for k in list_templates():
            print(k)
        return 0
    try:
        print(get(args.name))
        return 0
    except KeyError:
        print(f"[fitness] unknown template: {args.name}", file=sys.stderr)
        print(f"  available: {', '.join(list_templates())}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
