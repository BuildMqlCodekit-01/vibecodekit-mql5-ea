# Phase A Spec — Core Foundation

**Goal:** CPipNormalizer flagship + 4 commands + 4 scaffolds + 8 critical AP linter.
**Duration:** 3 weeks.
**Tag on completion:** v0.1.0.
**Prereq:** v0.0.1 (Phase 0 merged).

## Files added in Phase A (exhaustive list)

```
Include/
├── CPipNormalizer.mqh                        # FLAGSHIP — Plan v5 §6
├── CRiskGuard.mqh                            # daily-loss + max-positions
└── CMagicRegistry.mqh                        # file-backed magic reservation

scripts/
└── vibecodekit_mql5/
    ├── __init__.py
    ├── build.py                              # /mql5-build (< 200 LOC)
    ├── lint.py                               # /mql5-lint, 8 critical AP (< 200 LOC)
    ├── compile.py                            # /mql5-compile (< 150 LOC)
    └── pip_normalize.py                      # /mql5-pip-normalize (< 200 LOC)

scaffolds/
├── stdlib/
│   ├── netting/
│   │   ├── EAName.mq5
│   │   ├── Sets/default.set
│   │   └── README.md
│   ├── hedging/
│   └── python-bridge/
├── wizard-composable/
│   └── netting/
├── portfolio-basket/
│   ├── netting/
│   └── hedging/
└── ml-onnx/
    └── python-bridge/

tests/
├── gates/
│   └── phase-A/
│       ├── __init__.py
│       ├── test_phase_a_acceptance.py        # 3 e2e tests
│       ├── test_pipnormalizer.py             # 5 unit tests
│       ├── test_lint_8_critical_ap.py        # 8 unit tests
│       ├── test_build_scaffolds.py           # 4 unit tests
│       ├── test_compile_log_parser.py        # 3 unit tests
│       └── test_pip_normalize_refactor.py    # 5 unit tests
└── fixtures/
    ├── ap_01_no_sl.mq5
    ├── ap_03_lot_fixed.mq5
    ├── ap_05_overfitted.mq5
    ├── ap_15_raw_ordersend.mq5
    ├── ap_17_webrequest_ontick.mq5
    ├── ap_18_async_no_handler.mq5
    ├── ap_20_hardcoded_pip.mq5
    └── ap_21_jpy_xau_broken.mq5
```

## 28 tests (acceptance gate)

### 3 e2e tests
1. `test_pipnorm_4_digits_classes` — Init() correctly detects 5d/4d/3d/2d
2. `test_lint_8_critical_AP_detects_all` — 8 fixture .mq5 files trigger correct AP
3. `test_build_compile_stdlib` — `/mql5-build stdlib` → `/mql5-compile` → 0 errors

### 25 unit tests
- 5 CPipNormalizer (Init, Pips, LotForRisk, IsValidSLDistance, ClampSLPips)
- 8 lint detector (one per critical AP)
- 4 build scaffold (4 presets render correctly)
- 3 compile log parser (success, error, warning cases)
- 5 pip_normalize refactor (5 hardcoded patterns → kit calls)

## Module size constraints

| File | LOC ceiling | Responsibility |
|------|-------------|----------------|
| `Include/CPipNormalizer.mqh` | 250 | Cross-broker pip math |
| `Include/CRiskGuard.mqh` | 150 | Daily loss + position limit |
| `Include/CMagicRegistry.mqh` | 100 | Magic number file-backed registry |
| `scripts/.../build.py` | 200 | Render scaffold |
| `scripts/.../lint.py` | 200 | 8 critical AP detection |
| `scripts/.../compile.py` | 150 | MetaEditor CLI wrapper |
| `scripts/.../pip_normalize.py` | 200 | Auto-refactor hardcoded → kit |

## CPipNormalizer interface (per Plan v5 §6)

```cpp
class CPipNormalizer {
private:
    string m_symbol;
    int    m_digits;
    double m_point, m_pip, m_pip_in_points;
    double m_tick_size, m_tick_value, m_pip_value_per_lot;
    long   m_stops_level, m_freeze_level;
public:
    bool   Init(const string symbol = NULL);
    double Pips(int pips) const;
    double PriceToPips(double dist) const;
    double PipValue(int pips, double lots) const;
    double LotForRisk(double risk_$, int sl_pips) const;
    bool   IsValidSLDistance(int sl_pips) const;
    int    ClampSLPips(int desired) const;
};
```

Truth table: `pip = (digits ∈ {3,5}) ? 10*point : 1*point`.

## 8 critical anti-patterns (must be in `lint.py`)

| Code | Detector regex/AST |
|------|---------------------|
| AP-1 | OrderSend/CTrade.Buy without sl |
| AP-3 | `lot\s*=\s*\d+\.\d+` hardcoded |
| AP-5 | tester-set > 6 input + > 100k pass |
| AP-15 | direct `OrderSend(` not via CTrade |
| AP-17 | `WebRequest(` inside `OnTick`/`OnTimer` |
| AP-18 | `OrderSendAsync(` without `OnTradeTransaction(` |
| AP-20 | `\* 0\.000?1?`, `\* _Point`, `\* Point\(\)` |
| AP-21 | meta tag `// digits-tested:` < 2 classes |

## Acceptance gate

- [ ] v0.0.1 (Phase 0) merged
- [ ] All 28 tests pass on Linux + Windows runners
- [ ] `audit-plan-v5.py --post-phase=A` returns 0
- [ ] All Python modules < ceiling LOC
- [ ] No master `/mql5` command anywhere
- [ ] No query_loop / tool_executor / intent_router files exist
- [ ] 4 scaffolds render correctly
- [ ] /mql5-pip-normalize refactors fixture `ap_20_hardcoded_pip.mq5` correctly
- [ ] `git tag v0.1.0` after merge
