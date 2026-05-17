"""Phase E — gate suite for the post-build quality-matrix dashboard (P2.3).

Covers three layers:

* The pure :func:`dashboard.publish` hook (no command, stub command, failing
  command, missing command, timeout).
* The :func:`dashboard.render_from_pipeline` mapping (stage results land in
  the right matrix cells; ``--no-publish`` writes HTML but skips the hook).
* The end-to-end wiring inside ``auto_build.run_pipeline`` (every report
  carries a ``dashboard`` block; ``--no-dashboard`` skips it cleanly).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vibecodekit_mql5 import auto_build
from vibecodekit_mql5 import compile as compile_mod
from vibecodekit_mql5 import dashboard


# ─────────────────────────────────────────────────────────────────────────────
# publish() — the publish hook
# ─────────────────────────────────────────────────────────────────────────────

def test_publish_without_command_returns_file_uri(tmp_path: Path) -> None:
    html = tmp_path / "quality-matrix.html"
    html.write_text("<html></html>", encoding="utf-8")

    location = dashboard.publish(html, publish_cmd=None, env={})

    assert location.error is None
    assert location.command is None
    assert location.local_path == str(html)
    assert location.public_url is not None
    assert location.public_url.startswith("file://")


def test_publish_reads_env_when_no_explicit_command(tmp_path: Path) -> None:
    html = tmp_path / "quality-matrix.html"
    html.write_text("<html></html>", encoding="utf-8")
    # Stub command that just echoes a fixed URL.
    stub = tmp_path / "publish.sh"
    stub.write_text("#!/bin/bash\necho https://example.test/preview\n", encoding="utf-8")
    stub.chmod(0o755)

    location = dashboard.publish(html, env={dashboard.ENV_PUBLISH_CMD: str(stub)})

    assert location.error is None
    assert location.public_url == "https://example.test/preview"
    assert location.command == str(stub)


def test_publish_uses_last_nonblank_stdout_line(tmp_path: Path) -> None:
    """Many real publish backends print logs before the final URL."""
    html = tmp_path / "x.html"
    html.write_text("<html></html>", encoding="utf-8")
    stub = tmp_path / "noisy-publish.sh"
    stub.write_text(
        "#!/bin/bash\n"
        "echo 'uploading...'\n"
        "echo 'verifying...'\n"
        "echo ''\n"
        "echo https://cdn.test/abc\n",
        encoding="utf-8",
    )
    stub.chmod(0o755)

    location = dashboard.publish(html, publish_cmd=str(stub))

    assert location.public_url == "https://cdn.test/abc"
    assert location.error is None


def test_publish_command_failure_records_stderr(tmp_path: Path) -> None:
    html = tmp_path / "x.html"
    html.write_text("<html></html>", encoding="utf-8")
    stub = tmp_path / "broken.sh"
    stub.write_text(
        "#!/bin/bash\necho 'kaboom' >&2\nexit 9\n", encoding="utf-8"
    )
    stub.chmod(0o755)

    location = dashboard.publish(html, publish_cmd=str(stub))

    assert location.error is not None
    assert "exited 9" in location.error
    assert "kaboom" in location.error
    # We still fall back to the file:// path so callers can at least see it.
    assert location.public_url is not None and location.public_url.startswith("file://")


def test_publish_command_not_found(tmp_path: Path) -> None:
    html = tmp_path / "x.html"
    html.write_text("<html></html>", encoding="utf-8")

    location = dashboard.publish(html, publish_cmd="/does/not/exist/publisher")

    assert location.error is not None
    assert "publish command not found" in location.error
    assert location.public_url is not None
    assert location.public_url.startswith("file://")


def test_publish_html_missing(tmp_path: Path) -> None:
    location = dashboard.publish(tmp_path / "ghost.html")
    assert location.error is not None
    assert "not found" in location.error
    assert location.public_url is None


# ─────────────────────────────────────────────────────────────────────────────
# render_from_pipeline — stage results → matrix cells
# ─────────────────────────────────────────────────────────────────────────────

def test_render_from_pipeline_populates_matrix_cells(tmp_path: Path) -> None:
    digest = dashboard.PipelineDigest(
        name="ProbeEA",
        ok=True,
        stages=[
            {"name": "build",   "ok": True,  "skipped": False},
            {"name": "lint",    "ok": True,  "skipped": False},
            {"name": "compile", "ok": False, "skipped": False},
            {"name": "gate",    "ok": True,  "skipped": True},
        ],
    )
    html = dashboard.render_from_pipeline(digest)

    # Each axis label appears in the table header; counts include FAIL for
    # the broken compile cell and N/A for the skipped gate cell.
    assert "mql5 quality matrix" in html
    assert "PASS=" in html and "FAIL=" in html
    # The renderer paints FAIL cells with the FAIL colour.
    assert "#c62828" in html  # FAIL colour from rri.matrix._STATUS_COLORS


def test_write_dashboard_creates_html_file(tmp_path: Path) -> None:
    digest = dashboard.PipelineDigest(name="ProbeEA", ok=True, stages=[])
    out = tmp_path / "out"
    html_path = dashboard.write_dashboard(digest, out)

    assert html_path.is_file()
    assert html_path.parent == out
    assert html_path.read_text(encoding="utf-8").startswith("<!doctype html>")


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def test_cli_renders_and_skips_publish(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tmp_path / "dash"
    rc = dashboard.main([
        "--out-dir", str(out),
        "--name", "CliEA",
        "--stage", "build=ok",
        "--stage", "lint=ok",
        "--stage", "compile=fail",
        "--no-publish",
    ])
    assert rc == 0
    captured = capsys.readouterr().out
    parsed = json.loads(captured)
    assert parsed["public_url"].startswith("file://")
    assert parsed["error"] is None
    assert (out / "quality-matrix.html").is_file()


def test_cli_invokes_publish_command(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    stub = tmp_path / "publish.sh"
    stub.write_text(
        "#!/bin/bash\necho https://devin.example/build/42\n", encoding="utf-8"
    )
    stub.chmod(0o755)

    out = tmp_path / "dash"
    rc = dashboard.main([
        "--out-dir", str(out),
        "--name", "CliEA",
        "--stage", "build=ok",
        "--publish-cmd", str(stub),
    ])
    assert rc == 0
    parsed = json.loads(capsys.readouterr().out)
    assert parsed["public_url"] == "https://devin.example/build/42"
    assert parsed["error"] is None


def test_cli_publish_failure_exits_nonzero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    stub = tmp_path / "broken.sh"
    stub.write_text("#!/bin/bash\nexit 3\n", encoding="utf-8")
    stub.chmod(0o755)

    rc = dashboard.main([
        "--out-dir", str(tmp_path / "dash"),
        "--stage", "build=ok",
        "--publish-cmd", str(stub),
    ])
    assert rc == 1
    parsed = json.loads(capsys.readouterr().out)
    assert parsed["error"] is not None and "exited 3" in parsed["error"]


# ─────────────────────────────────────────────────────────────────────────────
# auto_build integration — dashboard attached to every report
# ─────────────────────────────────────────────────────────────────────────────

MINIMAL_SPEC: dict = {
    "name": "DashboardProbeEA",
    "preset": "stdlib",
    "stack": "netting",
    "symbol": "EURUSD",
    "timeframe": "H1",
    "mode": "personal",
}


def _patch_compile_success(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fake_compile(path, **_kwargs):
        ex5 = Path(str(path)).with_suffix(".ex5")
        ex5.write_bytes(b"stub")
        return compile_mod.CompileResult(success=True, ex5_path=str(ex5))

    monkeypatch.setattr(compile_mod, "compile_mq5", _fake_compile)


def _patch_orchestrator_pass(monkeypatch: pytest.MonkeyPatch) -> None:
    from vibecodekit_mql5.permission import orchestrator as orch_mod
    monkeypatch.setattr(
        orch_mod,
        "run",
        lambda _ns: orch_mod.OrchestratorReport(mode="personal", ok=True, layers=[]),
    )


def test_run_pipeline_attaches_dashboard_to_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_compile_success(monkeypatch)
    _patch_orchestrator_pass(monkeypatch)
    out = tmp_path / "build"
    report = auto_build.run_pipeline(dict(MINIMAL_SPEC), out)

    assert report.ok is True
    assert report.dashboard is not None
    assert report.dashboard.get("local_path", "").endswith("quality-matrix.html")
    # No publish command configured → file:// fallback URL.
    assert report.dashboard.get("public_url", "").startswith("file://")
    assert (out / "quality-matrix.html").is_file()


def test_run_pipeline_dashboard_emits_public_url_via_command(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_compile_success(monkeypatch)
    _patch_orchestrator_pass(monkeypatch)
    stub = tmp_path / "publish.sh"
    stub.write_text(
        "#!/bin/bash\necho https://devin.example/preview/abc\n", encoding="utf-8"
    )
    stub.chmod(0o755)

    report = auto_build.run_pipeline(
        dict(MINIMAL_SPEC),
        tmp_path / "build",
        publish_cmd=str(stub),
    )
    assert report.dashboard["public_url"] == "https://devin.example/preview/abc"
    assert report.dashboard["error"] is None


def test_run_pipeline_skip_dashboard(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_compile_success(monkeypatch)
    _patch_orchestrator_pass(monkeypatch)
    report = auto_build.run_pipeline(
        dict(MINIMAL_SPEC),
        tmp_path / "build",
        skip_dashboard=True,
    )
    assert report.dashboard == {"skipped": True}
    assert not (tmp_path / "build" / "quality-matrix.html").exists()


def test_run_pipeline_dashboard_emitted_on_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Even when a stage fails, the dashboard is still attached."""
    def _fake_compile(_path, **_kwargs):
        return compile_mod.CompileResult(
            success=False, errors=["fake: syntax error"], warnings=[]
        )
    monkeypatch.setattr(compile_mod, "compile_mq5", _fake_compile)

    report = auto_build.run_pipeline(
        dict(MINIMAL_SPEC),
        tmp_path / "build",
        skip_gate=True,
    )
    assert report.ok is False
    assert report.dashboard is not None
    assert report.dashboard.get("local_path", "").endswith("quality-matrix.html")


def test_main_cli_includes_dashboard_in_report_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _patch_compile_success(monkeypatch)
    _patch_orchestrator_pass(monkeypatch)

    import yaml
    spec_path = tmp_path / "spec.yaml"
    spec_path.write_text(yaml.safe_dump(dict(MINIMAL_SPEC)), encoding="utf-8")

    rc = auto_build.main([
        "--spec", str(spec_path),
        "--out-dir", str(tmp_path / "build"),
    ])
    assert rc == 0
    data = json.loads((tmp_path / "build" / "auto-build-report.json").read_text())
    assert "dashboard" in data
    assert data["dashboard"]["local_path"].endswith("quality-matrix.html")


def test_main_cli_publish_cmd_flag_overrides_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _patch_compile_success(monkeypatch)
    _patch_orchestrator_pass(monkeypatch)
    flag_stub = tmp_path / "flag.sh"
    flag_stub.write_text(
        "#!/bin/bash\necho https://flag-wins.test\n", encoding="utf-8"
    )
    flag_stub.chmod(0o755)
    env_stub = tmp_path / "env.sh"
    env_stub.write_text(
        "#!/bin/bash\necho https://env-loses.test\n", encoding="utf-8"
    )
    env_stub.chmod(0o755)
    monkeypatch.setenv(dashboard.ENV_PUBLISH_CMD, str(env_stub))

    import yaml
    spec_path = tmp_path / "spec.yaml"
    spec_path.write_text(yaml.safe_dump(dict(MINIMAL_SPEC)), encoding="utf-8")

    rc = auto_build.main([
        "--spec", str(spec_path),
        "--out-dir", str(tmp_path / "build"),
        "--publish-cmd", str(flag_stub),
    ])
    assert rc == 0
    data = json.loads((tmp_path / "build" / "auto-build-report.json").read_text())
    assert data["dashboard"]["public_url"] == "https://flag-wins.test"


def test_console_script_entry_point_resolves() -> None:
    """``mql5-dashboard`` is registered in pyproject.toml entry points."""
    import importlib.metadata as md
    eps = md.entry_points(group="console_scripts")
    names = {ep.name for ep in eps}
    assert "mql5-dashboard" in names
