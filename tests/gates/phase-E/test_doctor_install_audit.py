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


def test_doctor_reports_metaeditor_and_terminal_via_env(
    tmp_path: Path, monkeypatch
) -> None:
    """METAEDITOR_PATH / MQL5_TERMINAL_PATH overrides take precedence.

    Setup-wine-metaeditor.sh writes both to ~/.mql5-env after install, so doctor
    must find them on every fresh shell that sources that file.
    """
    me = tmp_path / "MetaEditor64.exe"
    term = tmp_path / "terminal64.exe"
    me.write_bytes(b"")
    term.write_bytes(b"")
    monkeypatch.setenv("METAEDITOR_PATH", str(me))
    monkeypatch.setenv("MQL5_TERMINAL_PATH", str(term))
    monkeypatch.delenv("WINEPREFIX", raising=False)
    rep = doctor.run_doctor(REPO_ROOT)
    by_name = {c["name"]: c for c in rep.checks}
    assert by_name["metaeditor-bin"]["ok"] is True
    assert by_name["metaeditor-bin"]["detail"] == str(me)
    assert by_name["terminal-bin"]["ok"] is True
    assert by_name["terminal-bin"]["detail"] == str(term)


def test_doctor_metaeditor_and_terminal_fail_with_useful_detail(
    tmp_path: Path, monkeypatch
) -> None:
    """When no probe path resolves, doctor must list what it tried.

    Regression: the previous `repo_root/.cache/metaeditor/MetaEditor64.exe`
    check always failed even on a fully-working Devin VM. The new probe list
    is order-sensitive, so verify the failure-detail names every candidate so
    operators can fix the install with one glance.
    """
    monkeypatch.delenv("METAEDITOR_PATH", raising=False)
    monkeypatch.delenv("MQL5_TERMINAL_PATH", raising=False)
    monkeypatch.setenv("WINEPREFIX", str(tmp_path / "empty"))
    monkeypatch.setenv("HOME", str(tmp_path / "empty-home"))
    rep = doctor.run_doctor(REPO_ROOT)
    by_name = {c["name"]: c for c in rep.checks}
    assert by_name["metaeditor-bin"]["ok"] is False
    # Failure detail must contain the env-var name (so an operator knows what
    # to set) AND the canonical Wine-prefix probe path.
    assert "METAEDITOR_PATH" in by_name["metaeditor-bin"]["detail"]
    assert "MetaEditor64.exe" in by_name["metaeditor-bin"]["detail"]
    assert by_name["terminal-bin"]["ok"] is False
    assert "MQL5_TERMINAL_PATH" in by_name["terminal-bin"]["detail"]
    assert "terminal64.exe" in by_name["terminal-bin"]["detail"]


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


def test_audit_all_probes_pass() -> None:
    """Regression: every probe in the 70-test conformance battery must report ok."""
    rep = audit.run_audit()
    failed = [p for p in rep.probes if not p.ok]
    assert failed == [], "audit probes failed: " + ", ".join(p.name for p in failed)
    assert rep.ok


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
