"""Permission Layer 5 — METHODOLOGY-GATE (RRI 8-step completed).

Asks :mod:`vibecodekit_mql5.rri.step_workflow` whether the steps required
by ``mode`` all have ``.done`` sentinels in the state directory.

This layer is only enforced for TEAM and ENTERPRISE modes. Personal mode
trivially passes — but we still emit a JSON report so the orchestrator
can show why the layer was skipped.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ..rri import step_workflow as sw


def gate(state_dir: Path, mode: str = "personal") -> dict:
    if mode not in sw.MODE_REQUIRED_STEPS:
        raise ValueError(f"unknown mode: {mode!r}")
    if mode == "personal":
        return {
            "ok": True,
            "mode": mode,
            "skipped": True,
            "reason": "personal mode does not require methodology gate",
            "state_dir": str(state_dir),
        }
    required = sw.required_steps(mode)
    completed = sw.completed_steps(state_dir) if state_dir.exists() else ()
    missing = [s for s in required if s not in completed]
    ok = not missing
    return {
        "ok": ok,
        "mode": mode,
        "state_dir": str(state_dir),
        "required_steps": list(required),
        "completed_steps": list(completed),
        "missing_steps": missing,
    }


def main() -> int:
    ap = argparse.ArgumentParser(prog="mql5-permission-layer5")
    ap.add_argument("--state-dir", type=Path, default=Path(".rri-state"))
    ap.add_argument("--mode", choices=tuple(sw.MODE_REQUIRED_STEPS), default="personal")
    args = ap.parse_args()
    result = gate(args.state_dir, args.mode)
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
