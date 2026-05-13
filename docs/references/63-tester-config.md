---
id: 63-tester-config
title: tester.ini configuration
tags: [tester, config]
applicable_phase: B
---

# tester.ini configuration

`tester.ini` controls every Strategy Tester run.  Key keys:

- `Expert` — EA name (without `.ex5`)
- `Symbol`, `Period`
- `FromDate`, `ToDate`
- `ForwardMode` (0 = none, 1 = 1/2, 2 = 1/3, 3 = 1/4, 4 = custom)
- `Model` (0 = every tick, 1 = 1-min OHLC, 2 = open prices, 3 = math
  calc, 4 = every tick based on real ticks)
- `Optimization` (0 = none, 1 = slow complete, 2 = Cloud Network,
  3 = fast genetic)
- `OptimizationCriterion` — enum 0..6 (see `cloud_optimize.py`)

`backtest.py` emits a tester.ini matching the kit's defaults.
