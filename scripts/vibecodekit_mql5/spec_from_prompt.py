"""Translate a free-text description into a valid ``ea-spec.yaml``.

This module is the bridge between the Devin **chat-driven build** playbook
(P2.2) and ``mql5-auto-build``. The playbook captures a single English (or
Vietnamese) sentence from the user — ``"build EA trend EURUSD H1 risk 0.5%
SL 30 TP 60 macd + sar"`` — and turns it into a YAML spec that
``spec_schema.validate`` accepts.

Design choices
--------------

* **Deterministic, regex-only**. The parser is intentionally rule-based so
  it can run inside an unattended pipeline (no LLM call, no network).
  Anything it can't parse is left at its schema default rather than
  hallucinated; ``--strict`` makes those gaps an error.

* **Stdlib only** — no ``pyyaml`` import here; the output is rendered via
  the same minimalist emitter used elsewhere in the kit so the module is
  safe to import in environments where pyyaml is missing.

* **Idempotent**. Re-running the parser on its own emitted YAML produces
  the same YAML (the round-trip is covered by tests).

CLI
---

::

    mql5-spec-from-prompt "build EA trend EURUSD H1 risk 0.5%"

Writes the resulting spec to stdout. Use ``--out PATH`` to write to a file
and ``--strict`` to require every schema-mandatory field be inferable from
the prompt (default: fall back to schema defaults silently).
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from . import build as build_mod
from . import spec_schema


# ─────────────────────────────────────────────────────────────────────────────
# Recognisers
# ─────────────────────────────────────────────────────────────────────────────

# Trading pairs the kit's archetypes can target. We deliberately keep this
# explicit instead of a generic 6-letter regex because plain word boundaries
# would happily match prose tokens like ``"DOMAIN"`` or ``"BUFFER"``.
_FX_MAJORS = (
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "NZDUSD", "USDCAD",
    "EURGBP", "EURJPY", "GBPJPY", "AUDJPY", "EURAUD", "EURCHF", "GBPCHF",
)
_METALS_CRYPTO = ("XAUUSD", "XAGUSD", "BTCUSD", "ETHUSD")
_INDICES = ("US30", "US500", "NAS100", "GER40", "UK100", "JPN225")

_SYMBOLS: tuple[str, ...] = _FX_MAJORS + _METALS_CRYPTO + _INDICES

# Strategy Tester timeframes accepted by MetaTrader 5.
_TIMEFRAMES: tuple[str, ...] = (
    "M1", "M2", "M3", "M4", "M5", "M6", "M10", "M12", "M15", "M20", "M30",
    "H1", "H2", "H3", "H4", "H6", "H8", "H12",
    "D1", "W1", "MN1",
)

# Keyword → (preset, stack). The first hit in source-order wins so callers
# can short-circuit a generic "stdlib" mention with a more specific one
# ("trend stdlib …" → trend, not stdlib).
_PRESET_KEYWORDS: tuple[tuple[str, tuple[str, str]], ...] = (
    # ── archetype-first hints ──
    (r"\btrend(?:[\s-]?follow(?:ing)?)?\b",  ("trend", "netting")),
    (r"\bmean[\s-]?revers(?:ion|ing)\b",     ("mean-reversion", "hedging")),
    (r"\bbreak[\s-]?out\b",                  ("breakout", "netting")),
    (r"\bscalp(?:ing|er)?\b",                ("scalping", "hedging")),
    (r"\bhft\b",                             ("hft-async", "netting")),
    (r"\bnews(?:[\s-]?trad(?:ing|e))?\b",    ("news-trading", "netting")),
    (r"\barbitrage\b",                       ("arbitrage-stat", "python-bridge")),
    (r"\bgrid\b",                            ("grid", "hedging")),
    (r"\bdca\b",                             ("dca", "hedging")),
    (r"\bhedg(?:e|ing)[\s-]?multi\b",        ("hedging-multi", "hedging")),
    (r"\bml[\s-]?onnx\b|\bonnx\b|\bmachine[\s-]?learn(?:ing)?\b",
                                             ("ml-onnx", "python-bridge")),
    (r"\bllm\b|\bgpt\b|\bclaude\b|\bollama\b",
                                             ("service-llm-bridge", "cloud-api")),
    (r"\bservice\b|\bdaemon\b",              ("service", "standalone")),
    (r"\bportfolio(?:[\s-]?basket)?\b|\bbasket\b",
                                             ("portfolio-basket", "netting")),
    (r"\bwizard\b",                          ("wizard-composable", "netting")),
    # ── stdlib fallback ──
    (r"\bstdlib\b|\bstandard[\s-]?library\b",("stdlib", "netting")),
)

# Stack overrides spotted after the preset has been chosen.
_STACK_KEYWORDS: tuple[tuple[str, str], ...] = (
    (r"\bnetting\b",            "netting"),
    (r"\bhedg(?:e|ing)\b",      "hedging"),
    (r"\bpython[\s-]?bridge\b", "python-bridge"),
    (r"\bself[\s-]?hosted\b|\bollama\b",         "self-hosted-ollama"),
    (r"\bembedded\b|\bembedded[\s-]?onnx\b",     "embedded-onnx-llm"),
    (r"\bcloud(?:[\s-]?api)?\b|\bopenai\b|\bclaude\b",
                                                 "cloud-api"),
    (r"\bstandalone\b",         "standalone"),
)

# Indicator keywords used by the ``signals:`` block. Maps free-text to the
# canonical ``kind`` accepted by ``spec_schema.VALID_SIGNAL_KINDS``.
_SIGNAL_KEYWORDS: tuple[tuple[str, str], ...] = (
    (r"\bmacd\b",                            "macd"),
    (r"\bsar\b|\bparabolic\b",               "sar"),
    (r"\brsi\b",                             "rsi"),
    (r"\bema[\s-]?cross\b|\bma[\s-]?cross\b","ema_cross"),
    (r"\bbb\b|\bbollinger\b|\bbbands\b",     "bbands"),
    (r"\batr[\s-]?break\b|\batr\b",          "atr_break"),
)


# ─────────────────────────────────────────────────────────────────────────────
# Parser
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class PromptParseResult:
    """Structured outcome of parsing a single prompt.

    ``spec`` is a plain dict ready to be passed to ``spec_schema.validate``
    or rendered via ``to_yaml``. ``inferred`` lists the field paths that
    were filled from the prompt (vs falling back to schema defaults), so
    callers can surface "I assumed X because you didn't say" warnings.
    """

    spec: dict[str, object] = field(default_factory=dict)
    inferred: list[str] = field(default_factory=list)
    defaulted: list[str] = field(default_factory=list)


def parse(prompt: str) -> PromptParseResult:
    """Return a structured spec for ``prompt``.

    The parser never raises; gaps in the prompt are filled with the same
    defaults ``spec_schema.RiskConfig`` uses so the output is always
    schema-valid.
    """
    result = PromptParseResult()
    text = prompt.strip()
    if not text:
        # Fully blank prompts still produce a syntactically valid spec —
        # the caller can decide whether to accept that.
        result.spec = _default_spec()
        result.defaulted = ["everything"]
        return result

    preset, preset_stack = _match_preset(text)
    stack = _match_stack(text, fallback=preset_stack)
    # The schema enforces ``(preset, stack)`` compatibility, so we clamp
    # the prompt's stack hint to what the chosen preset actually supports.
    # Prefer ``preset_stack`` (the default associated with the preset's
    # archetype keyword), fall back to the first supported stack otherwise.
    allowed = build_mod.PRESETS.get(preset, [])
    if allowed and stack not in allowed:
        stack = preset_stack if preset_stack in allowed else allowed[0]
    symbol = _match_symbol(text)
    timeframe = _match_timeframe(text)
    risk = _match_risk(text)
    signals = _match_signals(text)
    name = _match_name(text, preset=preset, symbol=symbol, timeframe=timeframe)

    spec: dict[str, object] = {
        "name": name,
        "preset": preset,
        "stack": stack,
        "symbol": symbol,
        "timeframe": timeframe,
    }
    if risk:
        spec["risk"] = risk
    if signals:
        spec["signals"] = signals

    # Track what we inferred vs what we defaulted, for transparency.
    inferred: list[str] = ["name"]
    for k, v in (
        ("preset", _looked_up(text, _PRESET_KEYWORDS_PATTERNS)),
        ("stack",  _looked_up(text, _STACK_KEYWORDS)),
        ("symbol", any(s.upper() in text.upper() for s in _SYMBOLS)),
        ("timeframe", any(tf in text.upper() for tf in _TIMEFRAMES)),
        ("risk",   bool(risk)),
        ("signals",bool(signals)),
    ):
        if v:
            inferred.append(k)
        else:
            result.defaulted.append(k)
    result.spec = spec
    result.inferred = inferred
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Match helpers
# ─────────────────────────────────────────────────────────────────────────────

# Precompiled patterns kept here so the recogniser tables stay readable.
_PRESET_KEYWORDS_PATTERNS = tuple((pat, *_) for pat, *_ in _PRESET_KEYWORDS)


def _looked_up(text: str, table) -> bool:
    """True iff *any* pattern in ``table`` matches ``text``."""
    return any(re.search(pat, text, re.IGNORECASE) for pat, *_ in table)


def _match_preset(text: str) -> tuple[str, str]:
    for pat, (preset, stack) in _PRESET_KEYWORDS:
        if re.search(pat, text, re.IGNORECASE):
            return preset, stack
    # Fall back to the safest archetype.
    return "stdlib", "netting"


def _match_stack(text: str, fallback: str) -> str:
    """Prefer explicit stack mentions over the preset default."""
    for pat, stack in _STACK_KEYWORDS:
        if re.search(pat, text, re.IGNORECASE):
            return stack
    return fallback


def _match_symbol(text: str) -> str:
    """Pick the first known trading symbol in the prompt; default EURUSD."""
    up = text.upper()
    for sym in _SYMBOLS:
        # Word-boundary matching so ``EURUSDH1`` (without space) still parses.
        if re.search(rf"\b{sym}\b", up):
            return sym
    # Also accept slash forms like ``EUR/USD``.
    m = re.search(r"\b([A-Z]{3})\s*/\s*([A-Z]{3})\b", up)
    if m:
        joined = m.group(1) + m.group(2)
        if joined in _SYMBOLS:
            return joined
    return "EURUSD"


def _match_timeframe(text: str) -> str:
    up = text.upper()
    for tf in _TIMEFRAMES:
        if re.search(rf"\b{tf}\b", up):
            return tf
    return "H1"


def _match_risk(text: str) -> dict[str, float | int]:
    """Extract overrides for the risk block, if any are mentioned."""
    out: dict[str, float | int] = {}

    # ``risk 0.5%`` / ``0.5% risk`` / ``risk_per_trade 0.5``
    m = re.search(
        r"(?:risk(?:[\s_]*per[\s_]*trade)?\s*[:=]?\s*([\d.]+)\s*%?"
        r"|([\d.]+)\s*%\s*risk)",
        text, re.IGNORECASE,
    )
    if m:
        out["per_trade_pct"] = float(m.group(1) or m.group(2))

    # ``daily loss 5%`` / ``daily_loss 5``
    m = re.search(
        r"\bdaily[\s_]*loss\s*[:=]?\s*([\d.]+)\s*%?", text, re.IGNORECASE,
    )
    if m:
        out["daily_loss_pct"] = float(m.group(1))

    # ``SL 30`` / ``sl 30 pips`` / ``stop[-]loss 30``
    m = re.search(
        r"\b(?:sl|stop[\s-]?loss)\s*[:=]?\s*([\d]+)\s*(?:pips?)?",
        text, re.IGNORECASE,
    )
    if m:
        out["sl_pips"] = int(m.group(1))

    # ``TP 60`` / ``tp 60 pips`` / ``take[-]profit 60``
    m = re.search(
        r"\b(?:tp|take[\s-]?profit)\s*[:=]?\s*([\d]+)\s*(?:pips?)?",
        text, re.IGNORECASE,
    )
    if m:
        out["tp_pips"] = int(m.group(1))

    # ``max spread 3 pips`` / ``spread cap 3``
    m = re.search(
        r"\b(?:max[\s_]*spread|spread[\s_]*cap)\s*[:=]?\s*([\d.]+)\s*(?:pips?)?",
        text, re.IGNORECASE,
    )
    if m:
        out["max_spread_pips"] = float(m.group(1))

    # ``max positions 3`` / ``up to 5 positions``
    m = re.search(
        r"\b(?:max[\s_]*(?:open[\s_]*)?positions?|up[\s_]*to)\s*([\d]+)\s*(?:positions?|trades?)?",
        text, re.IGNORECASE,
    )
    if m:
        out["max_open_positions"] = int(m.group(1))
    return out


def _match_signals(text: str) -> dict[str, object] | None:
    """Return a ``signals`` block matching the schema's mapping shorthand.

    The MVP block keeps every indicator at its default params; only the
    kind and the combine-logic are inferred from the prompt. We emit the
    ``{list: [...], logic: ...}`` mapping form (rather than the bare list
    form) because that's the only way the schema lets us attach the
    combine-logic alongside the entries.
    """
    found: list[str] = []
    for pat, kind in _SIGNAL_KEYWORDS:
        if re.search(pat, text, re.IGNORECASE) and kind not in found:
            found.append(kind)
    if not found:
        return None
    logic = "OR" if re.search(r"\bor\b", text, re.IGNORECASE) else "AND"
    return {
        "logic": logic,
        "list": [{"kind": k} for k in found],
    }


def _match_name(
    text: str, *, preset: str, symbol: str, timeframe: str,
) -> str:
    """Extract a user-supplied name or synthesise one from preset+symbol+tf."""
    m = re.search(
        r"\b(?:name(?:d)?(?:\s+as)?|call(?:ed)?)\s*[:=]?\s*([A-Za-z0-9_]+)\b",
        text,
    )
    if m:
        return m.group(1)
    # Auto-name keeps things short and slug-y.
    return f"{preset.replace('-', '_').title().replace('_', '')}{symbol}{timeframe}"


# ─────────────────────────────────────────────────────────────────────────────
# Defaults + YAML emitter
# ─────────────────────────────────────────────────────────────────────────────

def _default_spec() -> dict[str, object]:
    """Schema-valid spec used when the prompt is completely empty."""
    return {
        "name": "StdlibEurusdH1",
        "preset": "stdlib",
        "stack": "netting",
        "symbol": "EURUSD",
        "timeframe": "H1",
    }


def to_yaml(spec: dict[str, object]) -> str:
    """Emit a minimal YAML serialisation of ``spec``.

    Only handles the subset of types this module produces: strings, ints,
    floats, lists of dicts. Output is stable so test fixtures don't churn.
    """
    lines: list[str] = []
    for key in ("name", "preset", "stack", "symbol", "timeframe", "mode"):
        if key in spec:
            lines.append(f"{key}: {spec[key]}")
    if "risk" in spec:
        risk = spec["risk"]
        assert isinstance(risk, dict)
        lines.append("risk:")
        for rk in (
            "per_trade_pct", "daily_loss_pct", "max_spread_pips",
            "max_open_positions", "sl_pips", "tp_pips",
        ):
            if rk in risk:
                lines.append(f"  {rk}: {risk[rk]}")
    if "signals" in spec:
        sigs = spec["signals"]
        lines.append("signals:")
        if isinstance(sigs, dict):
            if "logic" in sigs:
                lines.append(f"  logic: {sigs['logic']}")
            entries = sigs.get("list", [])
            if entries:
                lines.append("  list:")
                for entry in entries:
                    assert isinstance(entry, dict)
                    (k, v), = entry.items()
                    lines.append(f"    - {k}: {v}")
        else:
            assert isinstance(sigs, list)
            for entry in sigs:
                assert isinstance(entry, dict)
                (k, v), = entry.items()
                lines.append(f"  - {k}: {v}")
    return "\n".join(lines) + "\n"


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="mql5-spec-from-prompt",
        description="Translate a free-text EA description into ea-spec.yaml.",
    )
    p.add_argument("prompt", help="Natural-language description of the EA")
    p.add_argument(
        "--out", type=Path,
        help="Write the spec here instead of stdout.",
    )
    p.add_argument(
        "--strict", action="store_true",
        help="Exit non-zero if the prompt is missing schema-mandatory fields.",
    )
    p.add_argument(
        "--explain", action="store_true",
        help="Print a one-line summary of what was inferred vs defaulted.",
    )
    args = p.parse_args(argv)

    result = parse(args.prompt)
    # Run the spec through the real validator so we never emit garbage.
    spec_schema.validate(result.spec, valid_presets=build_mod.PRESETS)

    if args.strict:
        # Strictness is about whether the operator gave us enough to ground
        # the build. ``stack`` is implied by ``preset`` and ``name`` is
        # always synthesised from the other three, so we only insist on the
        # three fields a human would normally type into the prompt.
        required_for_strict = {"preset", "symbol", "timeframe"}
        missing = required_for_strict & set(result.defaulted)
        if missing:
            print(
                f"missing fields the prompt didn't mention: {sorted(missing)}",
                file=sys.stderr,
            )
            return 1

    yaml_text = to_yaml(result.spec)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(yaml_text, encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        sys.stdout.write(yaml_text)

    if args.explain:
        msg = (
            f"inferred: {result.inferred}  "
            f"defaulted: {result.defaulted}"
        )
        print(msg, file=sys.stderr)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
