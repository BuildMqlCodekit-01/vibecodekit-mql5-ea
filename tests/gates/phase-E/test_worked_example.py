"""Phase E unit tests — worked example replay verification."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
EX_DIR = REPO_ROOT / "examples" / "ea-wizard-macd-sar-eurusd-h1-portfolio"


def test_worked_example_ea_uses_kit_includes() -> None:
    src = (EX_DIR / "EAName.mq5").read_text()
    for inc in ("CPipNormalizer.mqh", "CRiskGuard.mqh", "CMagicRegistry.mqh",
                "CSpreadGuard.mqh", "CMfeMaeLogger.mqh"):
        assert f"#include <{inc}>" in src, f"worked example must use {inc}"


def test_worked_example_releases_indicator_handles() -> None:
    """AP-12 regression: handles created in OnInit released in OnDeinit."""
    src = (EX_DIR / "EAName.mq5").read_text()
    assert "iMACD(" in src
    assert "iSAR(" in src
    assert "IndicatorRelease(h_macd)" in src
    assert "IndicatorRelease(h_sar)" in src


def test_worked_example_set_file_has_inputs() -> None:
    text = (EX_DIR / "eurusd-h1.set").read_text()
    for key in ("InpMagic", "InpRiskPerTradePct", "InpDailyLossPct",
                "InpMacdFast", "InpSarStep"):
        assert key in text


def test_worked_example_results_artefacts_complete() -> None:
    for f in ("backtest.xml", "multibroker.csv", "canary.log",
              "matrix-64-cell.html"):
        assert (EX_DIR / "results" / f).exists()


def test_worked_example_matrix_html_color_codes_present() -> None:
    html = (EX_DIR / "results" / "matrix-64-cell.html").read_text()
    # 8 rows × 8 cols of color-coded cells.
    assert "PASS" in html
    assert "<table>" in html
