"""Phase D LLM bridge unit tests — 6 cases (3 patterns × 2 axes).

Each scaffold is validated for:
- presence of the bridge include header + class name match
- presence of a rule-based fallback path (Trader-17 #14, #16)

The python-side wirer ``llm_context.wire_llm`` is also exercised for
each pattern.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from vibecodekit_mql5 import llm_context

REPO = Path(__file__).resolve().parents[3]
SCAFFOLDS = REPO / "scaffolds" / "service-llm-bridge"


@pytest.mark.parametrize(
    "pattern,header_cls",
    [
        ("cloud-api",          "LlmCloudApiBridge"),
        ("self-hosted-ollama", "LlmSelfHostedOllamaBridge"),
        ("embedded-onnx-llm",  "LlmEmbeddedOnnxLlmBridge"),
    ],
)
def test_scaffold_ships_with_fallback(pattern: str, header_cls: str) -> None:
    base = SCAFFOLDS / pattern
    assert (base / "EAName.mq5").exists()
    header = base / f"{header_cls}.mqh"
    assert header.exists(), f"missing header {header}"
    body = header.read_text(encoding="utf-8")
    assert "fallback" in body.lower() or "_fallback" in body, \
        "every LLM bridge must implement a rule-based fallback"


@pytest.mark.parametrize(
    "pattern", ["cloud-api", "self-hosted-ollama", "embedded-onnx-llm"],
)
def test_wire_llm_inserts_include(pattern: str, tmp_path: Path) -> None:
    mq5 = tmp_path / "EA.mq5"
    mq5.write_text(
        '#property strict\n\nint OnInit() { return INIT_SUCCEEDED; }\n',
        encoding="utf-8",
    )
    rep = llm_context.wire_llm(mq5, pattern)
    assert rep.ok
    body = mq5.read_text()
    expected_cls = llm_context._pattern_class(pattern)
    assert f'#include "{expected_cls}.mqh"' in body
    assert f"{expected_cls} llm;" in body
    assert "llm.Init(" in body
