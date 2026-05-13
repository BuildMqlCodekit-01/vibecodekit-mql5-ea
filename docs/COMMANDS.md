---
id: commands
title: Command catalog (~30 commands)
applicable_phase: E
---

# Command catalog

All commands callable directly via `python -m vibecodekit_mql5.<name>`.
No master `/mql5` router — every command stands alone.

## Discovery (4)
- `/mql5-scan`     — survey project tree, classify artefacts
- `/mql5-survey`   — match free-text strategy → scaffold archetype
- `/mql5-doctor`   — installation + environment health check
- `/mql5-audit`    — run 70-test conformance battery

## Plan (4)
- `/mql5-rri`       — open Step 2 RRI template
- `/mql5-vision`    — open Step 3 VISION template
- `/mql5-blueprint` — open Step 4 BLUEPRINT template
- `/mql5-tip`       — open Step 5 TIP template

## Build (8)
- `/mql5-build`             — render a scaffold
- `/mql5-wizard`            — render the wizard-composable scaffold
- `/mql5-pip-normalize`     — patch a .mq5 to use `CPipNormalizer`
- `/mql5-async-build`       — render the hft-async scaffold
- `/mql5-onnx-export`       — PyTorch/TF → ONNX (opset ≥ 14)
- `/mql5-onnx-embed`        — embed an `.onnx` into an `.mq5` via `#resource`
- `/mql5-llm-context`       — wire an LLM bridge into an existing EA
- `/mql5-forge-init`        — initialise an Algo Forge repo

## Verify (10)
- `/mql5-compile`             — MetaEditor build (Wine on Linux)
- `/mql5-lint`                — 8 critical anti-pattern detectors
- `/mql5-method-hiding-check` — build-aware AP-21 detector
- `/mql5-backtest`            — drive Strategy Tester
- `/mql5-walkforward`         — IS/OOS Sharpe correlation
- `/mql5-monte-carlo`         — 1000-sim bootstrap DD
- `/mql5-overfit-check`       — OOS/IS ratio across 4 metrics
- `/mql5-multibroker`         — N-broker stability orchestrator
- `/mql5-fitness`             — OnTester custom fitness emitter (5 templates)
- `/mql5-mfe-mae`             — per-trade MFE/MAE log analyser

## RRI methodology (3)
- `/mql5-rri-bt`     — Backtest review (5 personas × 7 dim × 8 axis)
- `/mql5-rri-rr`     — Risk & Robustness review
- `/mql5-rri-chart`  — Optional indicator-dev RRI

## Review (5)
- `/mql5-review`        — generic review opener
- `/mql5-eng-review`    — engineering review opener
- `/mql5-ceo-review`    — leadership review opener
- `/mql5-cso`           — strategy review opener
- `/mql5-investigate`   — incident investigation opener

## Deploy (3)
- `/mql5-deploy-vps`     — emit a MIGRATE-VPS.md checklist
- `/mql5-cloud-optimize` — emit a tester.ini for Cloud Network
- `/mql5-canary`         — 30-min post-deploy live monitor

## Ship (3)
- `/mql5-forge-pr` — push a PR to Algo Forge
- `/mql5-ship`     — `git tag` + push
- `/mql5-refine`   — classify a diff as tweak/patch/rework

## Other (4)
- `/mql5-broker-safety`   — verify pip-norm + multi-broker
- `/mql5-trader-check`    — Trader-17 checklist
- `/mql5-install`         — reconcile-install kit overlay
- `/mql5-second-opinion`  — one-shot lint + Trader-17 (optional)
