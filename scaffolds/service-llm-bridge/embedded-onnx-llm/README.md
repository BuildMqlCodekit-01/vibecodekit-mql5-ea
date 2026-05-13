# service-llm-bridge / embedded-onnx-llm

Embeds an ONNX-quantised small LLM (Phi-3 mini, TinyLlama 1B, etc.) as
an MQL5 resource. No network, no API key, no rate limit. The model
runs inside the MetaTrader process so inference latency is single-digit
milliseconds — safe to call directly from `OnTick()`.

**Required file:** `phi3_mini.onnx` placed alongside the .mq5. The
build system declares it via:

```cpp
#resource "phi3_mini.onnx"
```

The fallback is an MA(20)/MA(50) trend signal (Trader-17 #14 + #16).

Render via:

```bash
python -m vibecodekit_mql5.build service-llm-bridge \
    --name MyOnnxLlmEA --symbol EURUSD --tf M15 --stack embedded-onnx-llm
```

Then drop the `phi3_mini.onnx` into the rendered directory before
running `python -m vibecodekit_mql5.compile <ea>.mq5`.
