---
id: 62-mfe-mae
title: MFE / MAE per-trade
tags: [mfe, mae]
applicable_phase: B
---

# MFE / MAE per-trade

Maximum Favourable Excursion (MFE) is the highest unrealised
profit during a trade; Maximum Adverse Excursion (MAE) is the deepest
unrealised loss.  `CMfeMaeLogger.mqh` snapshots both at trade close
via the trade history API and writes a CSV row per trade.

The ratio MFE/|MAE| approximates the "left-on-the-table" coefficient
— values > 2 typically signal a too-tight take-profit.
