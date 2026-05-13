---
id: 57-monte-carlo
title: Monte Carlo bootstrap
tags: [monte-carlo, robustness]
applicable_phase: B
---

# Monte Carlo bootstrap

`monte_carlo.py` bootstraps the backtest trade list 1000 times
to estimate the 95th-percentile drawdown distribution.  Default
implementation samples *with replacement* from the realised trade
sequence (preserves trade distribution but breaks autocorrelation —
appropriate for trade-by-trade evaluation, NOT bar-by-bar).
