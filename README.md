# vibecodekit-mql5-ea

Vibecode methodology kit for MQL5 Expert Advisor development on MetaTrader 5.

> **Status:** v0.0.1 (Phase 0 — Bootstrap). Full v1.0.0 expected after 14-17 weeks.
> Implementation tracked in `docs/PLAN-v5.md`.

## Quick start (after v0.1.0)

```bash
# Install kit
pip install -e .

# Bootstrap fresh EA from scaffold
/mql5-build stdlib --name MyEA --symbol EURUSD --tf H1

# Audit + compile + ship
/mql5-lint MyEA/MyEA.mq5
/mql5-compile MyEA/MyEA.mq5
/mql5-pip-normalize MyEA/MyEA.mq5
```

## Documentation

- [Plan v5 (full)](docs/PLAN-v5.md) — 1089-line spec
- [Phase specs](docs/) — per-phase strict scope
- [Anti-patterns to avoid](docs/anti-patterns-AVOID.md) — what NOT to inherit from VCK-HU
- [References](docs/references/) — 26 cheatsheets (populated in Phase E)

## Phases

| Phase | Status | Tag | Goal |
|-------|--------|-----|------|
| 0 | Bootstrap | v0.0.1 | Wine + MetaEditor + CI |
| A | Core | v0.1.0 | CPipNormalizer + 4 commands + 4 scaffolds |
| B | Test | v0.2.0 | Tester + walk-forward + multi-broker |
| C | Methodology | v0.3.0 | RRI + 8x8 matrix + 7-layer permission |
| D | Tech 2024-2025 | v0.5.0 | ONNX + HFT async + Algo Forge + LLM |
| E | Polish | v1.0.0 | 26 refs + 3 MCP + worked example + canary |

## Anti-patterns avoided (per audit)

This kit does NOT inherit from VCK-HU:
- `query_loop.py` (244 LOC) + `tool_executor.py` (587 LOC) — dead code
- `intent_router.py` (683 LOC) + `pipeline_router.py` (273 LOC) — router pattern
- Master `/mql5` command — single-prompt master router

User invokes `/mql5-build`, `/mql5-lint`, etc. directly.

## License

MIT
