"""/mql5-doctor — kit installation + environment health check.

Phase E command.  Validates that everything the kit needs is reachable
on the current machine: Python toolchain, ``wine`` for MetaEditor,
``MetaEditor.exe`` itself, the kit's package importability, and the
presence of the 28 reference docs + 11 scaffold archetypes.

Exit code 0 = healthy.  Non-zero = at least one check failed.  The
JSON output enumerates every check so a CI workflow can decide which
to treat as fatal.
"""

from __future__ import annotations

import argparse
import importlib
import json
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_MODULES = [
    "vibecodekit_mql5.compile",
    "vibecodekit_mql5.lint",
    "vibecodekit_mql5.build",
    "vibecodekit_mql5.pip_normalize",
]

REQUIRED_SCAFFOLDS = [
    "stdlib/netting", "stdlib/hedging", "stdlib/python-bridge",
    "wizard-composable/netting", "portfolio-basket/netting",
    "portfolio-basket/hedging", "ml-onnx/python-bridge",
    "hft-async/netting",
    "service-llm-bridge/cloud-api",
    "service-llm-bridge/self-hosted-ollama",
    "service-llm-bridge/embedded-onnx-llm",
]


@dataclass
class DoctorReport:
    checks: list[dict] = field(default_factory=list)
    ok: bool = True

    def add(self, name: str, ok: bool, detail: str = "") -> None:
        self.checks.append({"name": name, "ok": ok, "detail": detail})
        if not ok:
            self.ok = False


def run_doctor(repo_root: Path = REPO_ROOT) -> DoctorReport:
    rep = DoctorReport()
    rep.add("python-version", sys.version_info >= (3, 10),
            f"{sys.version_info.major}.{sys.version_info.minor}")
    rep.add("wine", shutil.which("wine") is not None, "PATH")
    metaeditor = repo_root / ".cache" / "metaeditor" / "MetaEditor64.exe"
    rep.add("metaeditor-bin", metaeditor.exists(), str(metaeditor))
    for mod in REQUIRED_MODULES:
        try:
            importlib.import_module(mod)
            rep.add(f"import:{mod}", True)
        except ImportError as exc:
            rep.add(f"import:{mod}", False, str(exc))
    refs_dir = repo_root / "docs" / "references"
    rep.add("references-dir", refs_dir.exists(), str(refs_dir))
    if refs_dir.exists():
        n = len(list(refs_dir.glob("*.md")))
        rep.add("references-count", n >= 28, f"{n} refs")
    for scaffold in REQUIRED_SCAFFOLDS:
        p = repo_root / "scaffolds" / scaffold / "EAName.mq5"
        rep.add(f"scaffold:{scaffold}", p.exists(), str(p))
    return rep


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mql5-doctor")
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    args = parser.parse_args(argv)
    rep = run_doctor(Path(args.repo_root))
    print(json.dumps({"ok": rep.ok, "checks": rep.checks}, indent=2))
    return 0 if rep.ok else 1


if __name__ == "__main__":
    sys.exit(main())
