"""mql5-method-hiding-check — detect MQL5 inheritance hiding without `using`.

Plan v5 §14 — MetaEditor build 5260+ (May 2025) treats unqualified
method redefinition in a derived class as ERROR instead of WARNING.
Migrating EAs must add explicit ``using BaseClass::method;`` directives
to opt back into the legacy hiding behaviour or rename methods.

This detector uses a regex heuristic (full MQL5 AST is not feasible
inside the kit) and accepts ``// vck-mql5: hiding-ok`` annotations on
the offending line as an opt-out.

Severity is build-dependent:
    target_build  < 5260 → WARN  (legacy MetaEditor — backwards compat)
    target_build >= 5260 → ERROR (strict, ships behaviour change)

False-positive tolerance: ≤ 30%, enforced by tests/gates/phase-D.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

BUILD_STRICT_THRESHOLD = 5260

CLASS_DEF = re.compile(
    r"class\s+(?P<name>\w+)\s*(?::\s*public\s+(?P<base>\w+))?\s*\{",
)
METHOD_DEF = re.compile(
    r"^\s*(?:virtual\s+)?(?:[\w:<>,\s\*&]+?)\s+(?P<name>\w+)\s*\("
    r"(?P<args>[^)]*)\)\s*(?:const\s*)?(?:override\s*)?[;{]",
    re.MULTILINE,
)
USING_DIRECTIVE = re.compile(r"using\s+(?P<base>\w+)::(?P<method>\w+)\s*;")
HIDING_OK_PRAGMA = "// vck-mql5: hiding-ok"


@dataclass
class HidingIssue:
    file: str
    line: int
    derived_class: str
    base_class: str
    method: str
    severity: str  # WARN | ERROR
    fix_hint: str


@dataclass
class CheckReport:
    ok: bool
    path: str
    target_build: int
    issues: list[HidingIssue] = field(default_factory=list)

    def as_json(self) -> str:
        return json.dumps(
            {
                "ok": self.ok, "path": self.path, "target_build": self.target_build,
                "issues": [iss.__dict__ for iss in self.issues],
            },
            indent=2,
        )


def _collect_class_bodies(src: str) -> list[tuple[str, str | None, int, str]]:
    """Return list of (class_name, base_name, body_start_line, body_text)."""
    results: list[tuple[str, str | None, int, str]] = []
    for m in CLASS_DEF.finditer(src):
        name = m.group("name")
        base = m.group("base")
        start = m.end()
        depth = 1
        idx = start
        while idx < len(src) and depth > 0:
            c = src[idx]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
            idx += 1
        body = src[start: idx - 1]
        line_no = src[: m.start()].count("\n") + 1
        results.append((name, base, line_no, body))
    return results


def check_method_hiding(mq5_path: Path, target_build: int = 5260) -> CheckReport:
    if not mq5_path.exists():
        return CheckReport(False, str(mq5_path), target_build, [])
    src = mq5_path.read_text(encoding="utf-8", errors="replace")
    classes = _collect_class_bodies(src)
    by_name = {name: body for name, _, _, body in classes}

    severity = "ERROR" if target_build >= BUILD_STRICT_THRESHOLD else "WARN"
    issues: list[HidingIssue] = []

    for derived, base, body_line, body in classes:
        if not base or base not in by_name:
            continue
        base_methods = {m.group("name") for m in METHOD_DEF.finditer(by_name[base])}
        using_methods = {m.group("method") for m in USING_DIRECTIVE.finditer(body)
                         if m.group("base") == base}
        for m in METHOD_DEF.finditer(body):
            method_name = m.group("name")
            if method_name == derived or method_name == "~" + derived:
                continue  # ctor / dtor
            if method_name not in base_methods:
                continue
            if method_name in using_methods:
                continue
            line_in_body = body[: m.start()].count("\n")
            absolute_line = body_line + line_in_body
            # Check for hiding-ok pragma on the same or previous line.
            src_lines = src.splitlines()
            if absolute_line - 1 < len(src_lines):
                near = " ".join(src_lines[max(0, absolute_line - 2): absolute_line + 1])
                if HIDING_OK_PRAGMA in near:
                    continue
            issues.append(HidingIssue(
                file=str(mq5_path), line=absolute_line,
                derived_class=derived, base_class=base, method=method_name,
                severity=severity,
                fix_hint=f"add `using {base}::{method_name};` or annotate `{HIDING_OK_PRAGMA}`",
            ))
    return CheckReport(
        ok=not (severity == "ERROR" and issues),
        path=str(mq5_path), target_build=target_build, issues=issues,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mql5-method-hiding-check")
    parser.add_argument("mq5", help="Path to .mq5 / .mqh source")
    parser.add_argument("--build", type=int, default=BUILD_STRICT_THRESHOLD)
    args = parser.parse_args(argv)
    rep = check_method_hiding(Path(args.mq5), target_build=args.build)
    print(rep.as_json())
    return 0 if rep.ok else 1


if __name__ == "__main__":
    sys.exit(main())
