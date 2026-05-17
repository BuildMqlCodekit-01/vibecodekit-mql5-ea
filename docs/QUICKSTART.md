---
id: quickstart
title: Quickstart — 10 minutes to first compile
applicable_phase: E
---

# Quickstart

10 minutes from a fresh clone to your first compiled scaffold.

## 1. Setup

```bash
git clone https://github.com/BuildMqlCodekit-01/vibecodekit-mql5-ea
cd vibecodekit-mql5-ea
./scripts/setup-wine-metaeditor.sh        # ~3 minutes, requires Linux + Wine 8.0.2
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

## 2. Health check

```bash
python -m vibecodekit_mql5.doctor
```

Expect every probe to report `ok: true`.  If `wine` or `metaeditor-bin`
fails, re-run `setup-wine-metaeditor.sh`.

## 3. Build your first EA

```bash
python -m vibecodekit_mql5.build stdlib \
    --name FirstEA --symbol EURUSD --tf H1
```

Generates `FirstEA.mq5` from the `stdlib/netting` scaffold (the default
stack for `stdlib`). Pass `--stack hedging` or `--stack python-bridge`
to pick another stack. Magic number is derived deterministically from
`--name` (see `build._magic_for`); no `--magic` flag is needed.

## 4. Lint + compile

```bash
python -m vibecodekit_mql5.lint  FirstEA.mq5
python -m vibecodekit_mql5.compile FirstEA.mq5
```

`compile` returns 0 + a path to the produced `.ex5` on success.

## 5. One-shot auto-build (recommended after first compile)

Once `doctor` and the manual `build → lint → compile` triple work, you
can replace steps 3+4 with a single command. `mql5-auto-build` chains
scan → build → lint → compile → permission-gate → dashboard, writes a
structured `auto-build-report.json`, and (optionally) publishes the
quality-matrix HTML to a public URL.

```bash
# 5a. Free-text → schema-valid ea-spec.yaml (deterministic, no LLM call)
mql5-spec-from-prompt "build EA trend EURUSD H1 risk 0.5%" \
    --out ea-spec.yaml --explain

# 5b. Drive the whole pipeline against that spec
mql5-auto-build --spec ea-spec.yaml --out-dir build/FirstEA

# 5c. Read the verdict + dashboard URL
jq '{ok, stages: [.stages[] | {name, ok}], dashboard}' \
    build/FirstEA/auto-build-report.json
```

The report is idempotent — rerunning with the same spec produces the
same output. Configure `MQL5_DASHBOARD_PUBLISH_CMD` (or pass
`--publish-cmd`) to publish the rendered `quality-matrix.html` to
Vercel / S3 / scp+nginx; without it the dashboard exposes a `file://`
URL only. See [`docs/devin-chat-driven-build.md`](devin-chat-driven-build.md)
for the full chat-driven flow.

If an existing `.mq5` trips the 8 critical anti-patterns, run
`mql5-auto-fix` to apply the transformer loop (AP-1, 3, 5, 15, 17, 18,
20, 21) and re-lint in one go.

## 6. Where to next?

- `docs/COMMANDS.md` — full 50-command catalog (Discovery → Plan → Build
  → Verify → RRI → Review → Deploy → Ship → Other).
- `docs/devin-chat-driven-build.md` — chat → spec → auto-build → PR
  playbook for Devin.
- `examples/ea-wizard-macd-sar-eurusd-h1-portfolio/README.md` — full
  8-step worked example.
- `docs/references/` — 29-document reference shelf.
