//+------------------------------------------------------------------+
//| CAsyncTradeManager.mqh — OrderSendAsync helper + transaction lock|
//|                                                                   |
//| Wraps OrderSendAsync() with proper request_id tracking + an      |
//| OnTradeTransaction()-side reconciliation step. Designed for      |
//| HFT EAs that need sub-millisecond submission latency.            |
//|                                                                   |
//| AP-18 (async-no-handler) requires every async submitter to be    |
//| paired with OnTradeTransaction() — see the matching scaffold     |
//| template for the wired callback.                                  |
//+------------------------------------------------------------------+
#ifndef __CAsyncTradeManager_MQH__
#define __CAsyncTradeManager_MQH__

#include "CPipNormalizer.mqh"
// Note: no <Trade\Trade.mqh> required. We call OrderSendAsync() directly
// with the built-in MqlTradeRequest / MqlTradeResult structs and never
// touch the stdlib CTrade class. Keeping this file stdlib-free means the
// hft-async scaffold compiles on a fresh MetaEditor install (e.g. the
// Wine MetaEditor that ships with the kit's Phase 0 setup) without the
// MQL5/Include/ tree being bootstrapped first.

struct AsyncPending
  {
   ulong             request_id;
   string            symbol;
   ENUM_ORDER_TYPE   type;
   double            volume;
   ulong             timestamp_us;
  };

class CAsyncTradeManager
  {
private:
   ulong             m_magic;
   AsyncPending      m_pending[];

   bool              _send(const ENUM_ORDER_TYPE type, const string symbol,
                           const double lots, const double price,
                           const double sl, const double tp)
     {
      MqlTradeRequest req={};
      MqlTradeResult  res={};
      req.action   = TRADE_ACTION_DEAL;
      req.symbol   = symbol;
      req.volume   = lots;
      req.type     = type;
      req.price    = price;
      req.sl       = sl;
      req.tp       = tp;
      req.magic    = m_magic;
      req.deviation= 10;
      req.type_filling = ORDER_FILLING_IOC;
      if(!OrderSendAsync(req, res))
        {
         Print("[AsyncTM] OrderSendAsync err=", GetLastError());
         return false;
        }
      AsyncPending p;
      p.request_id = res.request_id;
      p.symbol     = symbol;
      p.type       = type;
      p.volume     = lots;
      p.timestamp_us = GetMicrosecondCount();
      const int sz = ArraySize(m_pending);
      ArrayResize(m_pending, sz+1);
      m_pending[sz] = p;
      return true;
     }

public:
                     CAsyncTradeManager(void):m_magic(0) { ArrayResize(m_pending, 0); }
   void              Init(const ulong magic) { m_magic = magic; }

   bool              SendBuyAsync(const string symbol, const double lots,
                                  const double sl, const double tp)
     {
      const double ask = SymbolInfoDouble(symbol, SYMBOL_ASK);
      return _send(ORDER_TYPE_BUY, symbol, lots, ask, sl, tp);
     }
   bool              SendSellAsync(const string symbol, const double lots,
                                   const double sl, const double tp)
     {
      const double bid = SymbolInfoDouble(symbol, SYMBOL_BID);
      return _send(ORDER_TYPE_SELL, symbol, lots, bid, sl, tp);
     }

   //--- called from OnTradeTransaction()
   void              OnTransactionResult(const MqlTradeTransaction &trans,
                                         const MqlTradeRequest &request,
                                         const MqlTradeResult &result)
     {
      const int sz = ArraySize(m_pending);
      for(int i=0;i<sz;i++)
        {
         if(m_pending[i].request_id == result.request_id)
           {
            const ulong dt = GetMicrosecondCount() - m_pending[i].timestamp_us;
            Print("[AsyncTM] reconciled req=", result.request_id,
                  " retcode=", trans.deal == 0 ? result.retcode : 10009,
                  " latency_us=", dt);
            // shift array
            for(int j=i;j<sz-1;j++) m_pending[j] = m_pending[j+1];
            ArrayResize(m_pending, sz-1);
            return;
           }
        }
     }

   int               PendingCount(void) const { return ArraySize(m_pending); }
  };

#endif // __CAsyncTradeManager_MQH__
