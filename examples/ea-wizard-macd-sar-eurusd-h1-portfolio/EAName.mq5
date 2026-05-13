//+------------------------------------------------------------------+
//| MacdSarEurUsdH1.mq5 — worked-example EA                          |
//| Plan v5 §19 worked example: wizard-composable MACD+SAR signal on |
//| EURUSD H1, sized via CRiskGuard, pip-normalised via              |
//| CPipNormalizer, MFE/MAE-logged via CMfeMaeLogger.                |
//+------------------------------------------------------------------+
#property strict
#property copyright "vibecodekit-mql5-ea"
#property version   "1.00"

#include <CPipNormalizer.mqh>
#include <CRiskGuard.mqh>
#include <CMagicRegistry.mqh>
#include <CSpreadGuard.mqh>
#include <CMfeMaeLogger.mqh>
#include <Trade/Trade.mqh>

input int    InpMagic            = 5001;
input double InpRiskPerTradePct  = 0.5;
input double InpDailyLossPct     = 2.0;
input int    InpMaxPositions     = 1;
input int    InpMaxSpreadPoints  = 30;
input int    InpMacdFast         = 12;
input int    InpMacdSlow         = 26;
input int    InpMacdSignal       = 9;
input double InpSarStep          = 0.02;
input double InpSarMax           = 0.2;

CPipNormalizer pip;
CRiskGuard     risk;
CMagicRegistry registry;
CSpreadGuard   spread;
CMfeMaeLogger  mfemae;
CTrade         trade;

int h_macd = INVALID_HANDLE;
int h_sar  = INVALID_HANDLE;

int OnInit(void)
  {
   if(!pip.Init(_Symbol)) return INIT_FAILED;
   risk.Init(InpDailyLossPct, InpMaxPositions, InpRiskPerTradePct);
   spread.Init(InpMaxSpreadPoints);
   trade.SetExpertMagicNumber(InpMagic);
   if(!registry.Check(InpMagic)) registry.Reserve(InpMagic, "MacdSarH1");
   h_macd = iMACD(_Symbol, _Period, InpMacdFast, InpMacdSlow, InpMacdSignal, PRICE_CLOSE);
   h_sar  = iSAR(_Symbol, _Period, InpSarStep, InpSarMax);
   if(h_macd == INVALID_HANDLE || h_sar == INVALID_HANDLE) return INIT_FAILED;
   return INIT_SUCCEEDED;
  }

void OnDeinit(const int reason)
  {
   if(h_macd != INVALID_HANDLE) IndicatorRelease(h_macd);
   if(h_sar  != INVALID_HANDLE) IndicatorRelease(h_sar);
  }

void OnTick(void)
  {
   if(!spread.IsAllowed(_Symbol)) return;
   double macd[2], signal[2], sar[1];
   if(CopyBuffer(h_macd, 0, 0, 2, macd) != 2) return;
   if(CopyBuffer(h_macd, 1, 0, 2, signal) != 2) return;
   if(CopyBuffer(h_sar,  0, 0, 1, sar)    != 1) return;
   bool macd_up   = macd[1] > signal[1] && macd[0] <= signal[0];
   bool macd_down = macd[1] < signal[1] && macd[0] >= signal[0];
   double price = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   if(macd_up && sar[0] < price)
      trade.Buy(risk.Lots(_Symbol), _Symbol);
   else if(macd_down && sar[0] > price)
      trade.Sell(risk.Lots(_Symbol), _Symbol);
   mfemae.OnTick(_Symbol);
  }

void OnTrade(void) { mfemae.OnTrade(_Symbol); }
