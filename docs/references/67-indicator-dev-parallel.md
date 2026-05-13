---
id: 67-indicator-dev-parallel
title: Indicator development workflow
tags: [indicator, dev]
applicable_phase: A
---

# Indicator development workflow

Indicator development runs parallel to EA development but
deploys independently — indicators are `.ex5` files dropped in
`MQL5/Indicators/`, EAs reference them via `iCustom()`.  The kit's
`indicator-only` scaffold is the canonical starting point.
