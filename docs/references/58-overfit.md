---
id: 58-overfit
title: Overfit detection
tags: [overfit, robustness]
applicable_phase: B
---

# Overfit detection

`overfit_check.py` emits a simple OOS/IS ratio across the 4
canonical metrics: net profit, profit factor, Sharpe, recovery factor.
Threshold (per Plan v5 §B): a strategy is considered "fit" only when
each ratio ≥ 0.5.  Below that, the in-sample fit dominates and the
strategy is unlikely to generalise.
