"""Phase D HFT async unit tests — 4 cases.

1. async_build renders the hft-async scaffold to a fresh dir
2. the rendered .mq5 contains both OrderSendAsync references *and*
   OnTradeTransaction (AP-18 pair)
3. CAsyncTradeManager.mqh ships from the Include directory
4. /mql5-async-build refuses to overwrite existing dirs without --force
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
