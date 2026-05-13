//+------------------------------------------------------------------+
//| LlmSelfHostedOllamaBridge.mqh — WebRequest -> Ollama localhost   |
//+------------------------------------------------------------------+
#ifndef __LlmSelfHostedOllamaBridge_MQH__
#define __LlmSelfHostedOllamaBridge_MQH__

class LlmSelfHostedOllamaBridge
  {
private:
   int               m_timeout_ms;
   string            m_endpoint;
   string            m_model;

   string            _fallback(const string symbol)
     {
      const double rsi = iRSI(symbol, _Period, 14, PRICE_CLOSE);
      if(rsi > 70.0) return "SELL";
      if(rsi < 30.0) return "BUY";
      return "FLAT";
     }

public:
                     LlmSelfHostedOllamaBridge(void)
                       : m_timeout_ms(5000),
                         m_endpoint("http://127.0.0.1:11434/api/generate"),
                         m_model("llama3.2") {}
   bool              Init(const int timeout_ms = 5000)
     { m_timeout_ms = timeout_ms; return true; }
   void              SetEndpoint(const string url) { m_endpoint = url; }
   void              SetModel(const string m)      { m_model    = m;   }

   string            SuggestOrFallback(const string symbol)
     {
      string payload = StringFormat("{\"model\":\"%s\",\"prompt\":"
                                    "\"Trend for %s now? Reply BUY|SELL|FLAT only.\","
                                    "\"stream\":false}", m_model, symbol);
      char post[]; StringToCharArray(payload, post, 0, WHOLECHAR_NULL, CP_UTF8);
      char result[]; string headers_out;
      int code = WebRequest("POST", m_endpoint,
                            "Content-Type: application/json\r\n",
                            m_timeout_ms, post, result, headers_out);
      if(code != 200) return _fallback(symbol);
      string body = CharArrayToString(result);
      if(StringFind(body, "BUY")  >= 0) return "BUY";
      if(StringFind(body, "SELL") >= 0) return "SELL";
      return "FLAT";
     }
  };

#endif
