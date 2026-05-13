//+------------------------------------------------------------------+
//| {{NAME}}.mq5                                                      |
//|                                                                   |
//| Scaffold:  service-llm-bridge / cloud-api                          |
//| Symbol:    {{SYMBOL}}                                              |
//| Timeframe: {{TF}}                                                  |
//|                                                                   |
//| WebRequest → OpenAI / Anthropic / Gemini chat completion.         |
//| Implements 5s timeout + rule-based fallback (Trader-17 #14, #16). |
//|                                                                   |
//| digits-tested: 5, 3                                                |
//+------------------------------------------------------------------+
#property copyright "vibecodekit-mql5-ea"
#property version   "1.00"
#property strict

#include "CPipNormalizer.mqh"
#include "CRiskGuard.mqh"
#include "CMagicRegistry.mqh"
#include "LlmCloudApiBridge.mqh"

input long   InpMagic        = 81200;
input double InpRiskMoney    = 100.0;
input int    InpSlPips       = 30;
input int    InpTpPips       = 60;
input double InpDailyLossPct = 0.05;
input int    InpMaxPositions = 3;
input int    InpLlmTimeoutMs = 5000;

CPipNormalizer       pip;
CRiskGuard           risk;
CMagicRegistry       registry;
LlmCloudApiBridge    llm;

int OnInit(void)
  {
   if(!pip.Init(_Symbol)) return INIT_FAILED;
   risk.Init(InpDailyLossPct, InpMaxPositions, 0.10);
   llm.Init(InpLlmTimeoutMs);
   if(!registry.Check(InpMagic))
      registry.Reserve(InpMagic, "{{NAME}}");
   return INIT_SUCCEEDED;
  }

void OnDeinit(const int reason) {}

// LLM call MUST NOT run in OnTick (AP-17). Run on OnTimer instead.
int OnTimer(void)
  {
   string action = llm.SuggestOrFallback(_Symbol);
   if(action == "BUY")  { /* place buy via stdlib trader */ }
   if(action == "SELL") { /* place sell via stdlib trader */ }
   return 0;
  }

void OnTick(void) { /* execution-only path; LLM lives in OnTimer */ }
