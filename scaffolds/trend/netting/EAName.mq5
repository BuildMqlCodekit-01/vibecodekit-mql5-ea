//+------------------------------------------------------------------+
//| {{NAME}}.mq5                                                      |
//|                                                                   |
//| Scaffold:  trend / netting                                       |
//| Symbol:    {{SYMBOL}}                                              |
//| Timeframe: {{TF}}                                                  |
//|                                                                   |
//| Trend-following EA: 50/200 MA cross with CPipNormalizer SL/TP.
//|                                                                   |
//| digits-tested: 5, 3                                                |
//+------------------------------------------------------------------+
#property copyright "vibecodekit-mql5-ea"
#property version   "1.00"
#property strict

#include "CPipNormalizer.mqh"
#include "CRiskGuard.mqh"
#include "CMagicRegistry.mqh"

input long   InpMagic        = 80100;
input double InpRiskMoney    = 100.0;
input int    InpSlPips       = 30;
input int    InpTpPips       = 60;
input double InpDailyLossPct = 0.05;
input int    InpMaxPositions = 3;

CPipNormalizer pip;
CRiskGuard     risk;
CMagicRegistry registry;

// MA handles — created once in OnInit (iMA returns a handle, not a value).
int h_fast = INVALID_HANDLE;
int h_slow = INVALID_HANDLE;

int OnInit(void)
  {
   if(!pip.Init(_Symbol)) return INIT_FAILED;
   risk.Init(InpDailyLossPct, InpMaxPositions, 0.10);
   if(!registry.Check(InpMagic))
      registry.Reserve(InpMagic, "{{NAME}}");
   h_fast = iMA(_Symbol, _Period, 50,  0, MODE_EMA, PRICE_CLOSE);
   h_slow = iMA(_Symbol, _Period, 200, 0, MODE_EMA, PRICE_CLOSE);
   if(h_fast == INVALID_HANDLE || h_slow == INVALID_HANDLE) return INIT_FAILED;
   Print("{{NAME}} initialized: symbol=", _Symbol, " pip=", pip.Pip());
   return INIT_SUCCEEDED;
  }

void OnDeinit(const int reason)
  {
   if(h_fast != INVALID_HANDLE) IndicatorRelease(h_fast);
   if(h_slow != INVALID_HANDLE) IndicatorRelease(h_slow);
  }

void OnTick(void)
  {
   // Fast/slow MA cross — placeholder strategy. Read values via CopyBuffer.
   double buf_fast[1], buf_slow[1];
   if(CopyBuffer(h_fast, 0, 0, 1, buf_fast) != 1) return;
   if(CopyBuffer(h_slow, 0, 0, 1, buf_slow) != 1) return;
   /* signal logic on buf_fast[0] vs buf_slow[0] */
  }
