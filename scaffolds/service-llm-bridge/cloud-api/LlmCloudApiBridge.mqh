//+------------------------------------------------------------------+
//| LlmCloudApiBridge.mqh — WebRequest -> Cloud chat completion       |
//|                                                                   |
//| Routes a per-symbol prompt to a configurable Cloud LLM endpoint  |
//| (OpenAI, Anthropic, Gemini) via WebRequest(). Enforces a 5-second |
//| timeout and falls back to a rule-based MA(20) trend signal if    |
//| the call fails or returns an empty payload.                       |
//+------------------------------------------------------------------+
#ifndef __LlmCloudApiBridge_MQH__
#define __LlmCloudApiBridge_MQH__

class LlmCloudApiBridge
  {
private:
   int               m_timeout_ms;
   string            m_endpoint;
   string            m_api_key;

   string            _rule_based_fallback(const string symbol)
     {
      double ma_fast = iMA(symbol, _Period, 20, 0, MODE_EMA, PRICE_CLOSE);
      double ma_slow = iMA(symbol, _Period, 50, 0, MODE_EMA, PRICE_CLOSE);
      if(ma_fast > ma_slow) return "BUY";
      if(ma_fast < ma_slow) return "SELL";
      return "FLAT";
     }

public:
                     LlmCloudApiBridge(void)
                       : m_timeout_ms(5000),
                         m_endpoint("https://api.openai.com/v1/chat/completions"),
                         m_api_key("") {}
   bool              Init(const int timeout_ms = 5000)
     { m_timeout_ms = timeout_ms; return true; }
   void              SetEndpoint(const string url) { m_endpoint = url; }
   void              SetApiKey(const string key)   { m_api_key  = key;  }

   string            SuggestOrFallback(const string symbol)
     {
      if(m_api_key == "") return _rule_based_fallback(symbol);

      string payload = StringFormat("{\"model\":\"gpt-4o-mini\","
                                    "\"messages\":[{\"role\":\"user\","
                                    "\"content\":\"Trend for %s now? Reply BUY|SELL|FLAT only.\"}]}",
                                    symbol);
      char post[]; StringToCharArray(payload, post, 0, WHOLECHAR_NULL, CP_UTF8);
      char result[]; string headers_out;
      int code = WebRequest("POST", m_endpoint,
                            "Authorization: Bearer " + m_api_key + "\r\n"
                            "Content-Type: application/json\r\n",
                            m_timeout_ms, post, result, headers_out);
      if(code != 200) return _rule_based_fallback(symbol);
      string body = CharArrayToString(result);
      if(StringFind(body, "BUY")  >= 0) return "BUY";
      if(StringFind(body, "SELL") >= 0) return "SELL";
      return "FLAT";
     }
  };

#endif
