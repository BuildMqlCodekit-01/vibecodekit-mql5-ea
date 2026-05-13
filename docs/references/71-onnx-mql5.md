---
id: 71-onnx-mql5
title: ONNX in MQL5 (build 4620+)
tags: [onnx, ml]
applicable_phase: D
---

# ONNX in MQL5 (build 4620+)

`#resource "model.onnx"` embeds the ONNX model into the
`.ex5`; `OnnxCreateFromBuffer` loads it at runtime; `OnnxRun` drives
inference.  Required opset ≥ 14 (see `onnx_export.py`).  Latency
budget per the kit: p95 ≤ 1 ms per tick (see AP-19).
