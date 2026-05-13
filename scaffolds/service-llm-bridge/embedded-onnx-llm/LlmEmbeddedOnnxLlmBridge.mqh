//+------------------------------------------------------------------+
//| LlmEmbeddedOnnxLlmBridge.mqh — local ONNX classifier wrapper      |
//+------------------------------------------------------------------+
#ifndef __LlmEmbeddedOnnxLlmBridge_MQH__
#define __LlmEmbeddedOnnxLlmBridge_MQH__

#include "COnnxLoader.mqh"

class LlmEmbeddedOnnxLlmBridge
  {
private:
   COnnxLoader      *m_onnx;
   string            _fallback(const string symbol)
     {
      const double ma_fast = iMA(symbol, _Period, 20, 0, MODE_EMA, PRICE_CLOSE);
      const double ma_slow = iMA(symbol, _Period, 50, 0, MODE_EMA, PRICE_CLOSE);
      if(ma_fast > ma_slow) return "BUY";
      if(ma_fast < ma_slow) return "SELL";
      return "FLAT";
     }

public:
                     LlmEmbeddedOnnxLlmBridge(void):m_onnx(NULL) {}
   bool              Init(COnnxLoader *onnx) { m_onnx = onnx; return true; }

   string            SuggestOrFallback(const string symbol)
     {
      if(m_onnx == NULL || m_onnx.Handle() == INVALID_HANDLE)
         return _fallback(symbol);
      float input[10]; float output[3];
      // toy feature: last 10 close-to-close returns
      for(int i = 0; i < 10; i++)
         input[i] = (float)(iClose(symbol, _Period, i) -
                            iClose(symbol, _Period, i + 1));
      if(!m_onnx.Run(input, 10, output, 3)) return _fallback(symbol);
      // argmax across 3 classes: 0=SELL, 1=FLAT, 2=BUY
      int best = 0;
      for(int i = 1; i < 3; i++) if(output[i] > output[best]) best = i;
      if(best == 0) return "SELL";
      if(best == 2) return "BUY";
      return "FLAT";
     }
  };

#endif
