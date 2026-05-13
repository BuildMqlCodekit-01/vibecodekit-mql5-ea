---
id: 73-cloud-network
title: Cloud Network optimisation
tags: [cloud, optimization]
applicable_phase: D
---

# Cloud Network optimisation

`Optimization=2` in `tester.ini` routes the optimisation
across the MQL5 Cloud Network.  Pricing: 0.001 USD/agent-second
(source: docs.mql5.com, 2024-10).  `cloud_optimize.py` computes the
budget from `passes × seconds-per-pass`.  PERSONAL mode rejects this
(too expensive); ENTERPRISE requires an explicit `--budget-usd` cap.
