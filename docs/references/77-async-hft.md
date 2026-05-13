---
id: 77-async-hft
title: Async HFT (OrderSendAsync)
tags: [async, hft]
applicable_phase: D
---

# Async HFT (OrderSendAsync)

`OrderSendAsync` posts the order and returns immediately;
the result arrives via `OnTradeTransaction`.  AP-18 enforces that any
EA calling `OrderSendAsync` also implements `OnTradeTransaction` — a
naked async order with no handler is unrecoverable.
