---
id: usage-en
title: vibecodekit-mql5-ea v1.0.0 Usage Guide (English)
applicable_phase: E
audience: end_user, dev_team
---

# `vibecodekit-mql5-ea` v1.0.0 Usage Guide

End-to-end walkthrough of all 43 commands, from idea to live shipping.
Suitable for both new users and dev teams.

> 📚 Vietnamese version: [USAGE-vi.md](USAGE-vi.md)
> 🛠️ Per-IDE / CLI integration: [ENV-SETUP-vi.md](ENV-SETUP-vi.md)

## Contents

1. [Environment setup](#1-environment-setup)
2. [The 8-step build philosophy](#2-the-8-step-build-philosophy)
3. [Commands by stage](#3-commands-by-stage)
4. [End-to-end example: MACD+SAR EURUSD H1](#4-end-to-end-example)
5. [Integrating the 3 MCP servers](#5-integrating-the-3-mcp-servers)
6. [22 anti-pattern detectors](#6-22-anti-pattern-detectors)
7. [Troubleshooting](#7-troubleshooting)

---

## 1. Environment setup

### 1.1. Requirements

| Component | Version |
|-----------|---------|
| Python | ≥ 3.10 |
| Wine | 8.0.2 (Linux/macOS) — MetaEditor is native on Windows |
| MetaEditor | build ≥ 5260 (so method-hiding lint stays at ERROR) |
| ONNX runtime | 1.14 (Phase D ONNX e2e) |
| Xvfb | optional — needed only on headless Linux CI |

### 1.2. Linux (Ubuntu 22.04+)

```bash
git clone https://github.com/BuildMqlCodekit-01/vibecodekit-mql5-ea
cd vibecodekit-mql5-ea

./scripts/setup-wine-metaeditor.sh        # ~3 min
python -m venv .venv && source .venv/bin/activate
pip install -e .

python -m vibecodekit_mql5.doctor         # every probe must show ok: true
```

### 1.3. macOS

Wine on macOS runs but is not officially supported by MetaQuotes.
Recommend a Devin VM or Linux VM. If you must run locally:

```bash
brew install --cask wine-stable
# Then same as Linux
```

### 1.4. Windows

MetaEditor is native, no Wine needed. PowerShell:

```powershell
git clone https://github.com/BuildMqlCodekit-01/vibecodekit-mql5-ea
cd vibecodekit-mql5-ea
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
python -m vibecodekit_mql5.doctor
```

> ⚠️ `setup-wine-metaeditor.sh` is bash-only — on Windows simply set
> `METAEDITOR_BIN` env var to your `metaeditor64.exe` path and skip
> the Wine step.

---

## 2. The 8-step build philosophy

Plan v5 splits the entire EA lifecycle into 8 steps. Each step has a
markdown template in `docs/rri-templates/` and a dedicated command:

| Step | Name | Open template | Output |
|------|------|---------------|--------|
| 1 | **SCAN** | `python -m vibecodekit_mql5.scan <dir>` | Project tree |
| 2 | **RRI** (Research / Risk / Robustness) | `python -m vibecodekit_mql5.rri --mode {personal,team,enterprise}` | `docs/rri-report.md` |
| 3 | **VISION** | `python -m vibecodekit_mql5.vision` | `docs/vision.md` |
| 4 | **BLUEPRINT** | `python -m vibecodekit_mql5.blueprint` | `docs/blueprint.md` |
| 5 | **TIP** (8 Technical Implementation Points) | `python -m vibecodekit_mql5.tip` | `docs/tip.md` |
| 6 | **BUILD** | `python -m vibecodekit_mql5.build <archetype>` or `wizard`, `async-build` | `.mq5` from scaffold |
| 7 | **VERIFY** | 10 commands from `compile` → `multibroker` | XML report + 64-cell matrix |
| 8 | **REFINE + SHIP** | `python -m vibecodekit_mql5.refine` + `ship` | Git tag + push |

### Mode breakdown

| Mode | RRI questions | Permission layers | Audience |
|------|---------------|-------------------|----------|
| `personal` | 5 q/persona × 6 = 30 | 1, 2, 3, 4, 7 | Solo trader |
| `team` | 12 q/persona × 6 = 72 | 1-5, 7 | 2–5-dev team |
| `enterprise` | 25 q/persona × 6 = 150 | 1-7 (full) | Org / fund |

---

## 3. Commands by stage

### 3.1. Discovery (4)

```bash
python -m vibecodekit_mql5.scan ~/projects/eurusd-portfolio
python -m vibecodekit_mql5.survey "MA cross strategy H1 trend following"
python -m vibecodekit_mql5.doctor
python -m vibecodekit_mql5.audit
```

### 3.2. Plan — template openers (4)

```bash
python -m vibecodekit_mql5.rri --mode team
python -m vibecodekit_mql5.vision
python -m vibecodekit_mql5.blueprint
python -m vibecodekit_mql5.tip
```

### 3.3. Build (8)

```bash
python -m vibecodekit_mql5.build stdlib --name MyEA --symbol EURUSD --tf H1
python -m vibecodekit_mql5.wizard --name MyWizardEA --symbol EURUSD --tf H1
python -m vibecodekit_mql5.async_build --name MyHftEA --symbol EURUSD --tf M1
python -m vibecodekit_mql5.pip_normalize MyEA.mq5
python -m vibecodekit_mql5.onnx_export model.pt --output model.onnx --opset 14
python -m vibecodekit_mql5.onnx_embed MyEA.mq5 --model model.onnx
python -m vibecodekit_mql5.llm_context MyEA.mq5 --pattern cloud-api
python -m vibecodekit_mql5.forge_init MyEA
```

Available archetypes for `build`: `stdlib`, `trend`, `mean-reversion`,
`breakout`, `scalping`, `hedging-multi`, `news-trading`,
`arbitrage-stat`, `library`, `indicator-only`, `grid`, `dca`,
`portfolio-basket`, `wizard-composable`, `hft-async`, `ml-onnx`,
`service-llm-bridge`.

LLM patterns: `cloud-api` | `self-hosted-ollama` | `embedded-onnx-llm`.

### 3.4. Verify (10)

```bash
python -m vibecodekit_mql5.compile             MyEA.mq5
python -m vibecodekit_mql5.lint                MyEA.mq5
python -m vibecodekit_mql5.method_hiding_check MyEA.mq5 --build 5260
python -m vibecodekit_mql5.backtest    --ea MyEA.ex5 --symbol EURUSD --period H1 \
    --from 2023.01.01 --to 2024.12.31
python -m vibecodekit_mql5.walkforward --ea MyEA.ex5 --windows 12
python -m vibecodekit_mql5.monte_carlo --report tester.xml --sims 1000
python -m vibecodekit_mql5.overfit_check --is is.xml --oos oos.xml
python -m vibecodekit_mql5.multibroker --ea MyEA.ex5 --brokers brokers.json
python -m vibecodekit_mql5.fitness     --template sharpe_recovery > OnTester.mq5
python -m vibecodekit_mql5.mfe_mae     --log mfe.csv --report mfe-report.html
```

### 3.5. RRI methodology (3)

```bash
python -m vibecodekit_mql5.rri.rri_bt    --report tester.xml --mode enterprise
python -m vibecodekit_mql5.rri.rri_rr    --report tester.xml
python -m vibecodekit_mql5.rri.rri_chart --symbol EURUSD --tf H1
```

### 3.6. Review openers (5)

```bash
python -m vibecodekit_mql5.review.review
python -m vibecodekit_mql5.review.eng_review
python -m vibecodekit_mql5.review.ceo_review
python -m vibecodekit_mql5.review.cso
python -m vibecodekit_mql5.review.investigate
```

### 3.7. Deploy (3)

```bash
python -m vibecodekit_mql5.deploy_vps      --ea MyEA.ex5 --vps-host myvps.example.com
python -m vibecodekit_mql5.cloud_optimize  --ea MyEA --budget-usd 50 --mode enterprise
python -m vibecodekit_mql5.canary          MyEA.ex5 --duration 30m
```

### 3.8. Ship (3)

```bash
python -m vibecodekit_mql5.forge_pr feature-branch --target main
python -m vibecodekit_mql5.ship --tag v1.0.1 --dry-run
python -m vibecodekit_mql5.ship --tag v1.0.1
python -m vibecodekit_mql5.refine --diff change.patch
```

### 3.9. Other (4)

```bash
python -m vibecodekit_mql5.broker_safety MyEA.mq5
python -m vibecodekit_mql5.trader_check  MyEA.mq5
python -m vibecodekit_mql5.install       ~/existing-mt5-project
python -m vibecodekit_mql5.second_opinion MyEA.mq5
```

---

## 4. End-to-end example

The full worked example lives at
`examples/ea-wizard-macd-sar-eurusd-h1-portfolio/`. It demonstrates a
**4-hour enterprise turnaround** on a Devin VM.

### Step 1 — SCAN (5 min)
```bash
python -m vibecodekit_mql5.scan ~/projects/eurusd-portfolio
```

### Step 2 — RRI (90 min, enterprise mode)
```bash
python -m vibecodekit_mql5.rri.step_workflow --mode enterprise
# 6 personas × 25 questions = 150 questions
# → docs/rri-report.md
```

### Step 3 — VISION (15 min)
Fill `docs/rri-templates/step-3-vision.md.tmpl`:
- Hypothesis: MACD signal cross gated by Parabolic-SAR flip
- Scope: EURUSD H1 netting account
- Out of scope: hedging, multi-symbol, news filter

### Step 4 — BLUEPRINT (30 min)
Pick:
- Archetype: `wizard-composable/netting`
- Includes: `CPipNormalizer`, `CRiskGuard`, `CMagicRegistry`, `CMfeMaeLogger`
- Magic: 5001

### Step 5 — TIP (8 TIPs, ~30 min)
8 Technical Implementation Points covering SL/TP, risk per trade,
filters, trailing, kill switch, slippage limit, news blackout, weekly
DD cap.

### Step 6 — BUILD (10 min)
```bash
python -m vibecodekit_mql5.wizard \
    --name EAMacdSarPortfolio \
    --symbol EURUSD --tf H1 \
    --output ~/projects/eurusd-portfolio
```

### Step 7 — VERIFY (multi-stage, ~60 min)
```bash
python -m vibecodekit_mql5.compile         EAMacdSarPortfolio.mq5
python -m vibecodekit_mql5.lint            EAMacdSarPortfolio.mq5
python -m vibecodekit_mql5.method_hiding_check EAMacdSarPortfolio.mq5
python -m vibecodekit_mql5.backtest        --ea EAMacdSarPortfolio.ex5 ...
python -m vibecodekit_mql5.walkforward     --ea EAMacdSarPortfolio.ex5 --windows 12
python -m vibecodekit_mql5.monte_carlo     --report tester.xml --sims 1000
python -m vibecodekit_mql5.overfit_check   --is is.xml --oos oos.xml
python -m vibecodekit_mql5.multibroker     --ea EAMacdSarPortfolio.ex5 --brokers 5
python -m vibecodekit_mql5.rri.rri_bt      --report tester.xml --mode enterprise
```

### Step 8 — REFINE + SHIP (~10 min)
```bash
python -m vibecodekit_mql5.refine --diff change.patch
python -m vibecodekit_mql5.ship --tag v1.0.0 --dry-run
python -m vibecodekit_mql5.ship --tag v1.0.0
```

Resulting artefacts in `results/`:
`EAMacdSarPortfolio.ex5`, `.set` file, 64-cell matrix HTML, backtest
XML, MFE/MAE report, canary log.

---

## 5. Integrating the 3 MCP servers

All three speak JSON-RPC 2.0 over stdio per the MCP spec. Usable from
any MCP client (Claude Desktop, Cursor, Codex, Devin, ...).

### 5.1. metaeditor-bridge

3 tools: `metaeditor.compile`, `metaeditor.parse_log`,
`metaeditor.includes_resolve`.

```bash
python mcp/metaeditor-bridge/server.py
```

### 5.2. mt5-bridge (READ-ONLY)

10 **read-only** tools (NO `order_send`, `order_close`, or
`position_modify` — enforced by `test_mt5_bridge_readonly_no_trade`):

- `mt5.symbols.list`, `mt5.symbol.info`
- `mt5.rates.copy`, `mt5.tick.last`
- `mt5.account.info`, `mt5.terminal.info`
- `mt5.positions.list`, `mt5.positions.history`
- `mt5.history.deals`, `mt5.market.book`

```bash
python mcp/mt5-bridge/server.py
```

### 5.3. algo-forge-bridge

6 tools: `forge.init`, `forge.clone`, `forge.commit`, `forge.pr.create`,
`forge.pr.list`, `forge.repo.list`. Requires `ALGO_FORGE_API_KEY`.

```bash
ALGO_FORGE_API_KEY=xxx python mcp/algo-forge-bridge/server.py
```

### 5.4. MCP client configuration

See [docs/ENV-SETUP-vi.md](ENV-SETUP-vi.md) for ready-to-paste configs
for Claude Desktop, Cursor, Codex, and Devin.

---

## 6. 22 anti-pattern detectors

Lint is split across two tiers:

### 6.1. Critical APs — ERROR, block ship (8)

| ID | Description | Detector |
|----|-------------|----------|
| AP-1 | `OrderSend` without SL | `lint.py` |
| AP-3 | Fixed lot size, not risk-based | `lint.py` |
| AP-5 | EA overfit (in-sample only) | `lint.py` |
| AP-15 | Raw `OrderSend` (no `CTrade`) | `lint.py` |
| AP-17 | `WebRequest` inside `OnTick` | `lint.py` |
| AP-18 | `OrderSendAsync` without `OnTradeTransaction` | `lint.py` |
| AP-20 | Hard-coded pip (`* 0.0001`, `* _Point`) | `lint.py` |
| AP-21 | JPY/XAU digits broken | `lint.py` |

### 6.2. Best-practice APs — WARN (13)

| ID | Description | Detector |
|----|-------------|----------|
| AP-2 | SL too tight | `lint_best_practice.py` |
| AP-4 | Martingale without cap | `lint_best_practice.py` |
| AP-6 | Curve-fitted optimisation | `lint_best_practice.py` |
| AP-7 | Hard-coded magic number | `lint_best_practice.py` |
| AP-8 | No spread guard | `lint_best_practice.py` |
| AP-9 | Multi-entry on same bar | `lint_best_practice.py` |
| AP-10 | `OrderSend` return not checked | `lint_best_practice.py` |
| AP-11 | EA mode-blind | `lint_best_practice.py` |
| AP-12 | Indicator handle leak | `lint_best_practice.py` |
| AP-13 | Broker-coupled EA | `lint_best_practice.py` |
| AP-14 | No MFE/MAE logging | `lint_best_practice.py` |
| AP-16 | Reinvent stdlib | `lint_best_practice.py` |
| AP-19 | ONNX without Strategy-Tester validation | `lint_best_practice.py` |

### 6.3. Method-hiding (1, build-aware)

MetaEditor build ≥ 5260 reports ERROR when a `CExpert` subclass has a
method with the same name as a base method without a
`using BaseClass::method;` directive. Build < 5260 only WARNs.

```bash
python -m vibecodekit_mql5.method_hiding_check MyEA.mq5 --build 5260
```

---

## 7. Troubleshooting

### "wine: command not found"
- Linux: `./scripts/setup-wine-metaeditor.sh` failed silently.
- macOS: `brew install --cask wine-stable`.
- Windows: set `METAEDITOR_BIN=C:\Path\To\metaeditor64.exe`.

### `doctor` reports "metaeditor-bin: not found"
```bash
export METAEDITOR_BIN=~/.wine/drive_c/Program\ Files/MetaTrader\ 5/metaeditor64.exe
```

### ONNX e2e test fails — torch not installed
```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install onnx onnxscript
```

### `audit-plan-v5.py --post-phase=E` reports missing scaffold
- Check `git status` for untracked scaffold files.
- Verify `.gitignore` isn't excluding artefacts:
  ```bash
  git check-ignore -v examples/**/results/canary.log
  ```

### mt5-bridge "MetaTrader5 not installed"
```bash
pip install MetaTrader5  # Windows or Wine MT5 desktop only
```

### `forge_init` returns 401 Unauthorized
```bash
export ALGO_FORGE_API_KEY=your_key_here
```

### Linguist classifies the repo as MQL4 instead of MQL5
- Fixed in `.gitattributes` (PR #17). After commit, wait ~10 min for
  GitHub to re-run Linguist.

---

## Further resources

- [`docs/COMMANDS.md`](COMMANDS.md) — 43-command reference card
- [`docs/references/`](references/) — 28 technical cheatsheets (50-survey → 79-pip-norm)
- [`docs/PLAN-v5.md`](PLAN-v5.md) — Original 1089-line spec
- [`docs/anti-patterns-AVOID.md`](anti-patterns-AVOID.md) — VCK-HU anti-patterns to avoid
- [`docs/rri-personas/`](rri-personas/) — 6 YAML × 25 q each
- [`docs/rri-templates/`](rri-templates/) — 8 step-by-step markdown templates
- [`examples/ea-wizard-macd-sar-eurusd-h1-portfolio/`](../examples/ea-wizard-macd-sar-eurusd-h1-portfolio/) — 4-hour worked example

Questions / bugs → open an issue at
https://github.com/BuildMqlCodekit-01/vibecodekit-mql5-ea/issues
