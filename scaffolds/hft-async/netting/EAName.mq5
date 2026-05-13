//+------------------------------------------------------------------+
//| {{NAME}}.mq5                                                      |
//|                                                                   |
//| Scaffold:  hft-async / netting                                     |
//| Symbol:    {{SYMBOL}}                                              |
//| Timeframe: {{TF}}                                                  |
//|                                                                   |
//| OrderSendAsync HFT shell with paired OnTradeTransaction reconciler|
//| (AP-18 compliant — async without handler is a critical error).    |
//|                                                                   |
//| digits-tested: 5, 3                                                |
//+------------------------------------------------------------------+
#property copyright "vibecodekit-mql5-ea"
#property version   "1.00"
#property strict

#include "CPipNormalizer.mqh"
#include "CRiskGuard.mqh"
#include "CMagicRegistry.mqh"
#include "CAsyncTradeManager.mqh"

input long   InpMagic        = 80050;
input double InpRiskMoney    = 50.0;
input int    InpSlPips       = 10;
input int    InpTpPips       = 15;
input double InpDailyLossPct = 0.02;
input int    InpMaxPositions = 5;

CPipNormalizer    pip;
CRiskGuard        risk;
CMagicRegistry    registry;
CAsyncTradeManager async_tm;

int OnInit(void)
  {
   if(!pip.Init(_Symbol)) return INIT_FAILED;
   risk.Init(InpDailyLossPct, InpMaxPositions, 0.10);
   async_tm.Init((ulong)InpMagic);
   if(!registry.Check(InpMagic))
      registry.Reserve(InpMagic, "{{NAME}}");
   Print("{{NAME}} HFT initialized; magic=", InpMagic);
   return INIT_SUCCEEDED;
  }

void OnDeinit(const int reason) {}

void OnTick(void)
  {
   // Signal placeholder — production EAs replace with their model output.
   // The async submitter latches each request_id so OnTradeTransaction can
   // reconcile the deal latency without polling.
  }

//+------------------------------------------------------------------+
//| OnTradeTransaction — AP-18 mandatory pair for OrderSendAsync     |
//+------------------------------------------------------------------+
void OnTradeTransaction(const MqlTradeTransaction &trans,
                        const MqlTradeRequest    &request,
                        const MqlTradeResult     &result)
  {
   async_tm.OnTransactionResult(trans, request, result);
  }
