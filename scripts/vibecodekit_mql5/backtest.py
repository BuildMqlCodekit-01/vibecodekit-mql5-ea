"""mql5-backtest — Strategy Tester wrapper.

Generates `tester.ini` from CLI args, invokes MetaTester via Wine, then
parses the XML report into a structured `BacktestResult`.

Result fields mirror the Plan v5 §12 metric list:
    PF, RF, Sharpe, GHPR, AHPR, EP, LRCorr, LRStdErr,
    MaxDrawdownPct, total_trades, profitable_pct,
    winning_streak, losing_streak, MFE/MAE correlation.

CLI:
    python -m vibecodekit_mql5.backtest <ea.ex5> <set.set> --period FROM-TO

Exit codes:
    0 — backtest ran + parsed
    1 — tester invocation or report-parse failure
    2 — argv / file-not-found error
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# Period parser  (FORMAT: "2023.01.01-2024.12.31"  or  "20230101-20241231")
# ─────────────────────────────────────────────────────────────────────────────

_PERIOD_RX = re.compile(
    r"^(?P<from>\d{4}[.\-]?\d{2}[.\-]?\d{2})-(?P<to>\d{4}[.\-]?\d{2}[.\-]?\d{2})$"
)


def parse_period(s: str) -> tuple[str, str]:
    """Return `(from, to)` in MT5 `YYYY.MM.DD` form. Raises `ValueError`."""
    m = _PERIOD_RX.match(s.strip())
    if not m:
        raise ValueError(f"period {s!r}: expected FROM-TO like 2023.01.01-2024.12.31")
    def _canon(d: str) -> str:
        d = d.replace("-", "").replace(".", "")
        if len(d) != 8:
            raise ValueError(f"period date {d!r}: 8 digits required")
        return f"{d[:4]}.{d[4:6]}.{d[6:]}"
    return _canon(m["from"]), _canon(m["to"])


# ─────────────────────────────────────────────────────────────────────────────
# tester.ini generator
# ─────────────────────────────────────────────────────────────────────────────

def render_tester_ini(
    *,
    ea_path: str,
    set_path: str,
    symbol: str,
    period: str,
    from_date: str,
    to_date: str,
    forward_mode: int = 0,
    report_path: str = "tester.xml",
    deposit: int = 10000,
    leverage: int = 100,
) -> str:
    """Render a minimal tester.ini. Caller owns paths (Wine drives accepted)."""
    return (
        "[Tester]\n"
        f"Expert={ea_path}\n"
        f"ExpertParameters={set_path}\n"
        f"Symbol={symbol}\n"
        f"Period={period}\n"
        f"FromDate={from_date}\n"
        f"ToDate={to_date}\n"
        f"ForwardMode={forward_mode}\n"
        f"Deposit={deposit}\n"
        f"Currency=USD\n"
        f"Leverage=1:{leverage}\n"
        "Model=1\n"  # 1 = 1-minute OHLC; 0 = every tick (slow)
        "Optimization=0\n"
        "ShutdownTerminal=1\n"
        f"Report={report_path}\n"
        "ReplaceReport=1\n"
    )


# ─────────────────────────────────────────────────────────────────────────────
# XML report parser
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class BacktestResult:
    symbol: str = ""
    period: str = ""
    profit_factor: float = 0.0
    recovery_factor: float = 0.0
    sharpe: float = 0.0
    ghpr: float = 0.0
    ahpr: float = 0.0
    expected_payoff: float = 0.0
    lr_correlation: float = 0.0
    lr_std_error: float = 0.0
    max_drawdown_pct: float = 0.0
    total_trades: int = 0
    profitable_pct: float = 0.0
    winning_streak: int = 0
    losing_streak: int = 0
    mfe_correlation: float = 0.0
    mae_correlation: float = 0.0
    broker_digits: int = 0
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


_FLOAT_FIELDS: dict[str, str] = {
    "ProfitFactor":    "profit_factor",
    "RecoveryFactor":  "recovery_factor",
    "SharpeRatio":     "sharpe",
    "GHPR":            "ghpr",
    "AHPR":            "ahpr",
    "ExpectedPayoff":  "expected_payoff",
    "LRCorrelation":   "lr_correlation",
    "LRStdError":      "lr_std_error",
    "MaxDrawdownPct":  "max_drawdown_pct",
    "ProfitablePct":   "profitable_pct",
    "MFECorrelation":  "mfe_correlation",
    "MAECorrelation":  "mae_correlation",
}
_INT_FIELDS: dict[str, str] = {
    "TotalTrades":     "total_trades",
    "WinningStreak":   "winning_streak",
    "LosingStreak":    "losing_streak",
    "BrokerDigits":    "broker_digits",
}


def _decode(raw: bytes) -> str:
    """MT5 writes reports as UTF-16-LE w/ BOM; tolerate UTF-8 fixtures too.

    UTF-16 codecs never raise on even-length byte streams, so we cannot rely
    on a try/except cascade. Sniff the BOM (or ASCII `<?xml` signature) up
    front to pick the right codec.
    """
    if raw.startswith(b"\xff\xfe"):
        return raw[2:].decode("utf-16-le", errors="replace")
    if raw.startswith(b"\xfe\xff"):
        return raw[2:].decode("utf-16-be", errors="replace")
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw[3:].decode("utf-8", errors="replace")
    # ASCII-range XML declaration → plain UTF-8.
    if raw.lstrip()[:5] in (b"<?xml", b"<Test"):
        return raw.decode("utf-8", errors="replace")
    # Heuristic: lots of NULs → some UTF-16 flavour without a BOM.
    if raw[:64].count(b"\x00") >= 16:
        return raw.decode("utf-16-le", errors="replace")
    return raw.decode("utf-8", errors="replace")


def parse_xml_report(text: str) -> BacktestResult:
    # Strip the bogus `encoding="UTF-16"` declaration if the bytes are already
    # decoded to a Python str — ElementTree refuses to re-decode declared-UTF-16.
    if text.lstrip().startswith("<?xml"):
        text = re.sub(r'encoding="[^"]+"', 'encoding="UTF-8"', text, count=1)
    root = ET.fromstring(text)
    out = BacktestResult()
    if (sym := root.findtext("Symbol")):
        out.symbol = sym.strip()
    if (per := root.findtext("Period")):
        out.period = per.strip()
    stats = root.find("Statistics")
    if stats is None:
        return out
    for tag, attr in _FLOAT_FIELDS.items():
        v = stats.findtext(tag)
        if v is not None:
            try: setattr(out, attr, float(v))
            except ValueError: pass
    for tag, attr in _INT_FIELDS.items():
        v = stats.findtext(tag)
        if v is not None:
            try: setattr(out, attr, int(v))
            except ValueError: pass
    return out


def parse_xml_report_file(path: Path) -> BacktestResult:
    return parse_xml_report(_decode(path.read_bytes()))


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="mql5-backtest", description=__doc__.splitlines()[0])
    p.add_argument("ea")
    p.add_argument("set_file")
    p.add_argument("--symbol", default="EURUSD")
    p.add_argument("--period", required=True)
    p.add_argument("--tf", default="H1")
    p.add_argument("--report", default=None, help="parse this existing XML (skip tester)")
    args = p.parse_args(argv)

    if args.report:
        result = parse_xml_report_file(Path(args.report))
        print(json.dumps(result.to_dict(), indent=2))
        return 0
    print("[mql5-backtest] running terminal is not implemented in Phase B unit-mode; "
          "pass --report <xml> to parse an existing report.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
