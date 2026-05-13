"""Phase E unit tests — doctor / install / audit / ship / refine / survey / scan."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from vibecodekit_mql5 import audit, doctor, install, refine, scan, ship, survey  # noqa: E402


def test_doctor_returns_report_with_checks() -> None:
    rep = doctor.run_doctor(REPO_ROOT)
    assert len(rep.checks) >= 10


def test_install_skips_when_target_already_has_file(tmp_path: Path) -> None:
    # Pre-populate the target with one Include header.
    incl = tmp_path / "Include" / "CPipNormalizer.mqh"
    incl.parent.mkdir(parents=True)
    incl.write_text("// user-modified\n", encoding="utf-8")
    rep = install.install(tmp_path, REPO_ROOT)
    assert any("CPipNormalizer.mqh" in s for s in rep.skipped)
    assert (tmp_path / "Include" / "CPipNormalizer.mqh.kit-template").exists()


def test_audit_runs_and_returns_probes() -> None:
    rep = audit.run_audit()
    assert len(rep.probes) >= 60


def test_ship_dry_run() -> None:
    rep = ship.ship("v0.0.0-test", dry_run=True)
    assert rep.tag == "v0.0.0-test"
    assert rep.pushed is False
    assert "dry-run" in rep.detail


def test_refine_tweak_for_set_only() -> None:
    diff = "diff --git a/eurusd.set b/eurusd.set\n--- a/eurusd.set\n+++ b/eurusd.set\n+InpMagic=5001\n"
    rep = refine.classify(diff)
    assert rep.classification == "tweak"


def test_refine_rework_for_big_logic_change() -> None:
    body = "\n".join([f"+new line {i}" for i in range(40)])
    diff = "diff --git a/EA.mq5 b/EA.mq5\n--- a/EA.mq5\n+++ b/EA.mq5\n" + body
    rep = refine.classify(diff)
    assert rep.classification == "rework"


def test_survey_picks_trend_for_ma_cross() -> None:
    rep = survey.survey("MA cross strategy on H1")
    assert rep.primary == "trend"


def test_survey_picks_scalping_for_tick() -> None:
    rep = survey.survey("low-latency scalping with tick precision")
    assert rep.primary == "scalping"


def test_scan_finds_kit_scaffold_files(tmp_path: Path) -> None:
    (tmp_path / "EA.mq5").write_text("// EA", encoding="utf-8")
    (tmp_path / "x.mqh").write_text("// inc", encoding="utf-8")
    rep = scan.scan_tree(tmp_path)
    assert rep.counts.get("ea-source") == 1
    assert rep.counts.get("include") == 1


def test_scan_returns_empty_report_for_missing_root(tmp_path: Path) -> None:
    rep = scan.scan_tree(tmp_path / "does-not-exist")
    assert rep.files == []
