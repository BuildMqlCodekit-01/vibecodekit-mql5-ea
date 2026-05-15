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

## 5. Where to next?

- `docs/COMMANDS.md` — full ~30-command catalog.
- `examples/ea-wizard-macd-sar-eurusd-h1-portfolio/README.md` — full
  8-step worked example.
- `docs/references/` — 28-document reference shelf.
