"""mql5-auto-build — single-command EA build pipeline.

Reads a YAML or JSON spec and runs, in order:

    1. build   — render scaffold + Include/.mqh → project dir
    2. lint    — 23 anti-pattern detectors on the rendered .mq5
    3. compile — MetaEditor (Wine on Linux) → .ex5  (skippable)
    4. gate    — permission.orchestrator in spec-declared mode (skippable)

Each stage is fail-fast: the first stage to fail aborts the pipeline.
A `report.json` summarising every stage is always written to
``<out_dir>/auto-build-report.json``, even on failure.

Spec schema (YAML or JSON, minimum required fields):

    name:      str  EA name; also the project dir + magic seed
    preset:    str  scaffold preset (trend, stdlib, ml-onnx, ...)
    stack:     str  scaffold stack (netting, hedging, python-bridge, ...)
    symbol:    str  trading symbol (EURUSD, XAUUSD, ...)
    timeframe: str  H1, M15, M5, ...
    mode:      str  optional; permission mode (personal/team/enterprise),
                    default "personal"

Usage:
    mql5-auto-build --spec ea-spec.yaml [--out-dir DIR] [--no-compile]
                    [--no-gate] [--force]

Exit codes:
    0 — pipeline succeeded
    1 — one stage failed (see report.json)
    2 — invocation error (bad spec, missing files, etc.)
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import build as build_mod
from . import compile as compile_mod
from . import lint as lint_mod
from . import spec_schema

# Kept for backward compat with anything that imported these constants from
# auto_build. The canonical source-of-truth now lives in spec_schema.
REQUIRED_FIELDS: tuple[str, ...] = spec_schema.REQUIRED_TOP_FIELDS
VALID_MODES: frozenset[str] = spec_schema.VALID_MODES


@dataclass
class StageResult:
    name: str
    ok: bool
    skipped: bool = False
    detail: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "ok": self.ok, "skipped": self.skipped, **self.detail}


@dataclass
class PipelineReport:
    spec: dict[str, Any]
    out_dir: str
    ok: bool = True
    stages: list[StageResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "spec": self.spec,
            "out_dir": self.out_dir,
            "ok": self.ok,
            "stages": [s.to_dict() for s in self.stages],
        }


def load_spec(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"spec not found: {path}")
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError(
                "YAML spec given but PyYAML not installed; "
                "`pip install pyyaml` or use a .json spec"
            ) from exc
        data = yaml.safe_load(text)
    else:
        data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError(f"spec must be a mapping, got {type(data).__name__}")
    return data


def validate_spec(spec: dict[str, Any]) -> spec_schema.EaSpec:
    """Validate ``spec`` and return a populated :class:`EaSpec`.

    Delegates to :func:`spec_schema.validate` so the schema (required fields,
    risk bounds, signal kinds) lives in exactly one place. Raises ``ValueError``
    on bad input so the existing ``main()`` error-handling path keeps working
    — ``SpecValidationError`` is a subclass of ``ValueError``.
    """
    return spec_schema.validate(spec, valid_presets=build_mod.PRESETS)


def _stage_build(
    spec: dict[str, Any],
    out_dir: Path,
    force: bool,
    ea_spec: spec_schema.EaSpec | None = None,
) -> StageResult:
    # Validated EaSpec carries risk + signals/filters/hooks for template
    # substitution and signals.md emission. When ``ea_spec`` is None (e.g. a
    # direct caller that bypassed validate_spec) fall back to defaults.
    extras: dict[str, str] = {}
    extra_files: list[tuple[str, str]] = []
    if ea_spec is not None:
        extras = ea_spec.risk.as_template_vars()
        if ea_spec.signals or ea_spec.filters:
            extra_files.append(("signals.md", spec_schema.render_signals_doc(ea_spec)))

    req = build_mod.BuildRequest(
        preset=spec["preset"],
        name=spec["name"],
        symbol=spec["symbol"],
        tf=spec["timeframe"],
        stack=spec["stack"],
        out_dir=out_dir,
        scaffolds_root=build_mod.DEFAULT_SCAFFOLDS,
        include_root=build_mod.DEFAULT_INCLUDE,
        force=force,
        extras=extras,
        extra_files=extra_files,
    )
    try:
        result_dir = build_mod.build(req)
    except (ValueError, FileNotFoundError, FileExistsError) as exc:
        return StageResult("build", ok=False, detail={"error": str(exc)})
    files = sorted(str(p.relative_to(result_dir)) for p in result_dir.rglob("*") if p.is_file())
    return StageResult("build", ok=True, detail={"out_dir": str(result_dir), "files": files})


def _stage_lint(mq5_path: Path) -> StageResult:
    findings = lint_mod.lint_file(mq5_path)
    errors = [f for f in findings if f.severity == "ERROR"]
    warnings = [f for f in findings if f.severity == "WARN"]
    return StageResult(
        "lint",
        ok=not errors,
        detail={
            "errors": [f.format() for f in errors],
            "warnings": [f.format() for f in warnings],
            "n_errors": len(errors),
            "n_warnings": len(warnings),
        },
    )


def _stage_compile(mq5_path: Path) -> StageResult:
    result = compile_mod.compile_mq5(mq5_path)
    data = result.to_dict()
    return StageResult(
        "compile",
        ok=bool(data.get("success")),
        detail={
            "errors": data.get("errors", []),
            "warnings": data.get("warnings", []),
            "ex5_path": data.get("ex5_path", ""),
        },
    )


def _stage_gate(mq5_path: Path, mode: str) -> StageResult:
    # Lazy import — orchestrator pulls in all 7 layers, keep startup light.
    from .permission import orchestrator as orch_mod

    ns = argparse.Namespace(
        source=mq5_path,
        mode=mode,
        compile_log=None,
        trader_check_report=None,
        state_dir=Path(".rri-state"),
        matrix=None,
        multibroker=None,
        journal=None,
    )
    report = orch_mod.run(ns)
    return StageResult(
        "gate",
        ok=report.ok,
        detail={"mode": report.mode, "layers": report.layers},
    )


def run_pipeline(
    spec: dict[str, Any],
    out_dir: Path,
    skip_compile: bool = False,
    skip_gate: bool = False,
    force: bool = False,
    ea_spec: spec_schema.EaSpec | None = None,
) -> PipelineReport:
    report = PipelineReport(spec=spec, out_dir=str(out_dir))

    build_stage = _stage_build(spec, out_dir, force, ea_spec=ea_spec)
    report.stages.append(build_stage)
    if not build_stage.ok:
        report.ok = False
        return report

    mq5_path = out_dir / f"{spec['name']}.mq5"
    if not mq5_path.is_file():
        # Some scaffolds rename the .mq5 differently; fall back to the first
        # .mq5 under the project dir.
        candidates = sorted(out_dir.glob("*.mq5"))
        if not candidates:
            report.stages.append(StageResult("lint", ok=False, detail={"error": "no .mq5 produced"}))
            report.ok = False
            return report
        mq5_path = candidates[0]

    lint_stage = _stage_lint(mq5_path)
    report.stages.append(lint_stage)
    if not lint_stage.ok:
        report.ok = False
        return report

    if skip_compile:
        report.stages.append(StageResult("compile", ok=True, skipped=True))
    else:
        compile_stage = _stage_compile(mq5_path)
        report.stages.append(compile_stage)
        if not compile_stage.ok:
            report.ok = False
            return report

    if skip_gate:
        report.stages.append(StageResult("gate", ok=True, skipped=True))
        return report
    gate_stage = _stage_gate(mq5_path, spec.get("mode", "personal"))
    report.stages.append(gate_stage)
    if not gate_stage.ok:
        report.ok = False
    return report


def _write_report(report: PipelineReport, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "auto-build-report.json"
    path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="mql5-auto-build", description=__doc__.splitlines()[0])
    ap.add_argument("--spec", required=True, type=Path, help="YAML or JSON spec file")
    ap.add_argument("--out-dir", type=Path, default=None,
                    help="output directory (default: ./<spec.name>)")
    ap.add_argument("--no-compile", action="store_true",
                    help="skip MetaEditor compile stage (useful without Wine)")
    ap.add_argument("--no-gate", action="store_true",
                    help="skip permission.orchestrator stage")
    ap.add_argument("--force", action="store_true",
                    help="overwrite existing output directory")
    args = ap.parse_args(argv)

    try:
        spec = load_spec(args.spec)
        ea_spec = validate_spec(spec)
    except (FileNotFoundError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"mql5-auto-build: {exc}", file=sys.stderr)
        return 2

    out_dir = args.out_dir or Path.cwd() / spec["name"]
    report = run_pipeline(
        spec,
        out_dir,
        skip_compile=args.no_compile,
        skip_gate=args.no_gate,
        force=args.force,
        ea_spec=ea_spec,
    )
    report_path = _write_report(report, out_dir)
    print(json.dumps(report.to_dict(), indent=2))
    print(f"\nreport: {report_path}", file=sys.stderr)
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
