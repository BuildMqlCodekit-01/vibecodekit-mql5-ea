---
id: 77-async-hft
title: Async HFT (OrderSendAsync)
tags: [async, hft, ap-18]
applicable_phase: D
---

# Async HFT (OrderSendAsync)

`OrderSendAsync` posts the order and returns immediately; the result
arrives asynchronously via `OnTradeTransaction`. The kit's flagship
`CAsyncTradeManager.mqh` (`Include/CAsyncTradeManager.mqh`) wraps this
correctly and keeps a per-request reconciliation queue so the HFT
scaffold never ships a "naked" async submission.

## API surface (`CAsyncTradeManager`)

| Method | Purpose |
|---|---|
| `void Init(ulong magic)` | bind the manager to a magic number (also matched on incoming `OnTradeTransaction`) |
| `bool SendBuyAsync(symbol, lots, sl, tp)` | post a market BUY via `OrderSendAsync`, record `request_id` |
| `bool SendSellAsync(symbol, lots, sl, tp)` | post a market SELL via `OrderSendAsync`, record `request_id` |
| `void OnTransactionResult(trans, result, request)` | call from `OnTradeTransaction` — pops the matching pending entry, prints latency in µs |
| `int  PendingCount()` | number of still-unreconciled `request_id`s |

Internally each pending submission stores `(request_id, symbol, type,
volume, timestamp_us)` so the reconciliation step can emit a real
submission-to-confirmation latency in microseconds, which is the only
honest signal for HFT EAs.

## Wiring the handler

```mql5
#include <CAsyncTradeManager.mqh>

CAsyncTradeManager async;

int OnInit(void) { async.Init(InpMagic); return INIT_SUCCEEDED; }

void OnTick(void)
  {
   if(/* signal */)
      async.SendBuyAsync(_Symbol, lots, sl, tp);   // returns immediately
  }

void OnTradeTransaction(const MqlTradeTransaction &trans,
                        const MqlTradeRequest &req,
                        const MqlTradeResult  &res)
  {
   async.OnTransactionResult(trans, res, req);
  }
```

## Anti-pattern hook — AP-18

`scripts/vibecodekit_mql5/lint.py:detect_ap18` scans for any
`OrderSendAsync(` call; if the same translation unit lacks an
`OnTradeTransaction(` definition the linter raises an `ERROR`:

```
EAName.mq5:42:3: ERROR AP-18: OrderSendAsync without OnTradeTransaction handler
```

This is intentionally a hard ERROR: an async submitter without a
matching handler is unrecoverable — request_ids leak, latency stats
are unmeasurable, and partial-fills go silent.

## Scaffold

```bash
python -m vibecodekit_mql5.async_build --name FastEA --symbol EURUSD --tf M1
```

renders the `scaffolds/hft-async/` archetype, which pre-wires both
`CAsyncTradeManager` and the matching `OnTradeTransaction` block so the
EA passes AP-18 out of the box.
