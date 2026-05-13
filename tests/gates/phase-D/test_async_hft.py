"""Phase D HFT async unit tests — 5 cases.

1. async_build renders the hft-async scaffold to a fresh dir
2. the rendered .mq5 contains both OrderSendAsync references *and*
   OnTradeTransaction (AP-18 pair)
3. CAsyncTradeManager.mqh ships from the Include directory
4. /mql5-async-build refuses to overwrite existing dirs without --force
5. CAsyncTradeManager.mqh must NOT pull in stock MQL5 stdlib headers
   (regression for the v1.0.1 demo finding — a stray `<Trade\\Trade.mqh>`
   include caused fresh Wine MetaEditor installs to fail with error 106).
"""

from __future__ import annotations

from pathlib import Path


from vibecodekit_mql5 import async_build

REPO = Path(__file__).resolve().parents[3]


def test_async_build_renders_hft_scaffold(tmp_path: Path) -> None:
    out = tmp_path / "MyHftEA"
    rc = async_build.main(
        ["--name", "MyHftEA", "--symbol", "EURUSD", "--tf", "M1",
         "--output", str(out)],
    )
    assert rc == 0
    mq5 = out / "MyHftEA.mq5"
    assert mq5.exists()


def test_rendered_hft_pairs_async_with_transaction(tmp_path: Path) -> None:
    out = tmp_path / "PairCheck"
    async_build.main(
        ["--name", "PairCheck", "--symbol", "EURUSD", "--tf", "M1",
         "--output", str(out)],
    )
    text = (out / "PairCheck.mq5").read_text()
    assert "OnTradeTransaction" in text  # AP-18 enforced at template level
    # the async manager is the only place OrderSendAsync lives in this scaffold
    mgr = (out / "CAsyncTradeManager.mqh").read_text()
    assert "OrderSendAsync" in mgr


def test_async_trade_manager_ships_from_include() -> None:
    mgr_path = REPO / "Include" / "CAsyncTradeManager.mqh"
    assert mgr_path.exists(), "CAsyncTradeManager.mqh must ship in Include/"
    body = mgr_path.read_text()
    assert "class CAsyncTradeManager" in body
    assert "OrderSendAsync" in body
    assert "OnTransactionResult" in body


def test_async_trade_manager_has_no_stdlib_includes() -> None:
    """CAsyncTradeManager.mqh uses only built-in MQL5 types
    (MqlTradeRequest, MqlTradeResult, OrderSendAsync, etc.) — it must
    NOT pull in stock MQL5 stdlib headers like <Trade\\Trade.mqh>,
    <Indicators\\Indicators.mqh>, <Arrays\\Arrays.mqh>.

    Keeping this file stdlib-free means hft-async scaffolds compile on
    a fresh MetaEditor install (e.g. the Wine MetaEditor that ships
    with the kit's Phase 0 setup) without the MQL5/Include tree being
    bootstrapped first. A stray include here caused the v1.0.1 deep-
    test demo to fail with: `error 106: file 'Trade\\Trade.mqh' not
    found`.
    """
    import re

    mgr_path = REPO / "Include" / "CAsyncTradeManager.mqh"
    body = mgr_path.read_text()

    # An include line that targets a stdlib path looks like:
    #   #include <Trade\Trade.mqh>
    # but must not match comment lines or include-guards. Use a regex
    # anchored to start-of-line to avoid false-positives in narrative
    # comments.
    pattern = re.compile(
        r"^\s*#include\s*<[^>]+>",
        re.MULTILINE,
    )
    matches = pattern.findall(body)
    assert matches == [], (
        f"CAsyncTradeManager.mqh must use only project-local includes "
        f"(quoted, not angle-bracket). Found stdlib includes: {matches}"
    )


def test_async_build_refuses_overwrite_without_force(tmp_path: Path) -> None:
    out = tmp_path / "NoOverwrite"
    async_build.main(
        ["--name", "NoOverwrite", "--symbol", "EURUSD", "--tf", "M1",
         "--output", str(out)],
    )
    # second call without --force must fail (return non-zero)
    rc = async_build.main(
        ["--name", "NoOverwrite", "--symbol", "EURUSD", "--tf", "M1",
         "--output", str(out)],
    )
    assert rc != 0
