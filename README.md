# vibecodekit-mql5-ea

[![version](https://img.shields.io/badge/version-v1.0.0-blue)](https://github.com/BuildMqlCodekit-01/vibecodekit-mql5-ea/releases/tag/v1.0.0)
[![tests](https://img.shields.io/badge/tests-234%20passing-success)]()
[![lint](https://img.shields.io/badge/ruff-clean-success)]()
[![license](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)

> **Vibecode methodology kit** for building production-grade MQL5 Expert
> Advisors on MetaTrader 5. Forty-three CLI commands, three MCP servers,
> twenty-eight reference cheatsheets, twenty-two anti-pattern detectors,
> and one fully worked 4-hour wizard-composable portfolio EA — all
> delivered as a flat, router-free, fail-fast toolkit.

📘 **Docs:** [Quickstart](docs/QUICKSTART.md) · [Full usage guide (EN)](docs/USAGE-en.md) · [Hướng dẫn đầy đủ (VN)](docs/USAGE-vi.md) · [Per-IDE setup](docs/ENV-SETUP-vi.md) · [Command catalog](docs/COMMANDS.md) · [Plan v5](docs/PLAN-v5.md)

---

## English

### What you get in v1.0.0

| Layer | Shipped |
|-------|---------|
| **Commands** | 43 (`/mql5-{scan,survey,doctor,audit,rri,vision,blueprint,tip,build,wizard,pip-normalize,async-build,onnx-export,onnx-embed,llm-context,forge-init,compile,lint,method-hiding-check,backtest,walkforward,monte-carlo,overfit-check,multibroker,fitness,mfe-mae,rri-bt,rri-rr,rri-chart,review,eng-review,ceo-review,cso,investigate,deploy-vps,cloud-optimize,canary,forge-pr,ship,refine,broker-safety,trader-check,install}`) |
| **MCP servers** | 3 (`metaeditor-bridge`, `mt5-bridge` READ-ONLY, `algo-forge-bridge`) |
| **Reference docs** | 28 (`docs/references/50-survey.md` → `79-pip-norm.md`) |
| **Scaffolds** | 22 archetypes × broker variants (`scaffolds/trend/netting`, `scalping/hedging`, `hft-async/netting`, `service-llm-bridge/{cloud-api,self-hosted-ollama,embedded-onnx-llm}`, `ml-onnx/python-bridge`, …) |
| **Anti-pattern detectors** | 22 (8 critical `ERROR` + 13 best-practice `WARN` + 1 build-aware method-hiding) |
| **Quality matrix** | 8 dimensions × 8 axes = 64-cell HTML report (PASS / WARN / FAIL / N/A) |
| **Permission layers** | 7 (source-lint → compile → AP-lint → checklist → methodology → quality-matrix → broker-safety) |
| **Mode-aware orchestrator** | PERSONAL (layers 1/2/3/4/7) · TEAM (1-5,7) · ENTERPRISE (1-7) |
| **Trader checklist** | 17 items (`trader-check`) with 15/17 PASS threshold |
| **Worked example** | `examples/ea-wizard-macd-sar-eurusd-h1-portfolio/` — 4-hour enterprise turnaround |
| **Test gate** | 234 tests passing across Phase 0/A/B/C/D/E |

### Quick start (5 minutes)

```bash
git clone https://github.com/BuildMqlCodekit-01/vibecodekit-mql5-ea
cd vibecodekit-mql5-ea
./scripts/setup-wine-metaeditor.sh        # Linux only; ~3 min
python -m venv .venv && source .venv/bin/activate
pip install -e .

python -m vibecodekit_mql5.doctor         # health check
python -m vibecodekit_mql5.build stdlib --name FirstEA --symbol EURUSD --tf H1
python -m vibecodekit_mql5.lint    FirstEA.mq5
python -m vibecodekit_mql5.compile FirstEA.mq5
```

Detailed walk-throughs:
- New users — [docs/USAGE-en.md](docs/USAGE-en.md)
- Dev teams + worked example — [examples/ea-wizard-macd-sar-eurusd-h1-portfolio/README.md](examples/ea-wizard-macd-sar-eurusd-h1-portfolio/README.md)
- IDE / CLI integration — [docs/ENV-SETUP-vi.md](docs/ENV-SETUP-vi.md)

### Phase history

| Phase | Tag | Theme | Highlights |
|-------|-----|-------|-----------|
| 0 | `v0.0.1` | Bootstrap | Wine 8.0.2 + headless MetaEditor + Xvfb + CI |
| A | `v0.1.0` | Core foundation | `CPipNormalizer`, `CRiskGuard`, `CMagicRegistry`, 8 critical AP detectors, 3 stdlib scaffolds |
| B | `v0.2.0` | Test & validation | Strategy Tester driver, walk-forward, Monte-Carlo, multi-broker, Trader-17 checklist |
| C | `v0.3.0` | Methodology | 6 RRI personas × 25 q × 3 modes, 8-step workflow, 64-cell quality matrix, 7-layer permission orchestrator |
| D | `v0.5.0` | Tech 2024-2025 | ONNX runtime 1.14 export/embed, HFT async (`OrderSendAsync` + `OnTradeTransaction`), Algo Forge, LLM bridge (3 patterns), Cloud Network optimize, method-hiding linter |
| **E** | **`v1.0.0`** | **Polish & ship** | **28 reference docs, 3 MCP servers, `/mql5-canary`, 4-hour worked example** |

### Anti-patterns this kit refuses to ship

This kit was forked from a methodology study of `vibecodekit-handwritten`
(`VCK-HU`). It deliberately does **not** re-inherit any of the following
hot-spots:

- `query_loop.py`, `tool_executor.py`, `intent_router.py`,
  `pipeline_router.py` — dead routers & god modules
- Master `/mql5` single-prompt entrypoint — every command stands alone
- LLM hallucination of test results — every "passes" claim must be
  traceable to a Strategy Tester XML report
- `OrderSend` without `MarketInfo`-aware `CPipNormalizer` — broker
  digits/point asymmetry breaks pip math on JPY/XAU
- ONNX inference that was never validated against a real Strategy Tester
  run (caught by AP-19)
- `OrderSendAsync` without an `OnTradeTransaction` handler (caught by
  AP-18)
- `WebRequest` calls inside `OnTick` (caught by AP-17)
- Method-hiding on `CExpert` subclass without `using BaseClass::method;`
  (caught on MetaEditor build ≥ 5260)

---

## Tiếng Việt

### v1.0.0 có gì

| Thành phần | Đã giao |
|-----------|---------|
| **Lệnh CLI** | 43 lệnh — đầy đủ chu trình `scan → plan → build → verify → review → deploy → ship` |
| **MCP server** | 3 (`metaeditor-bridge`, `mt5-bridge` chỉ-đọc, `algo-forge-bridge`) — chuẩn MCP JSON-RPC 2.0 over stdio |
| **Tài liệu tham khảo** | 28 cheatsheet (`docs/references/50-survey.md` → `79-pip-norm.md`) |
| **Scaffold** | 22 archetype × biến thể tài khoản (`trend/netting`, `scalping/hedging`, `hft-async/netting`, 3 biến thể LLM bridge, ml-onnx, …) |
| **Bộ dò chống mẫu xấu** | 22 detector (8 lỗi nghiêm trọng `ERROR` + 13 best-practice `WARN` + 1 method-hiding theo build) |
| **Ma trận chất lượng** | 8 chiều × 8 trục = 64 ô HTML (PASS / WARN / FAIL / N/A) |
| **Lớp permission** | 7 lớp (source-lint → compile → AP-lint → checklist → methodology → quality-matrix → broker-safety) |
| **Mode orchestrator** | PERSONAL (lớp 1/2/3/4/7) · TEAM (1-5, 7) · ENTERPRISE (1-7) |
| **Trader checklist** | 17 mục (`trader-check`), ngưỡng pass 15/17 |
| **Ví dụ hoàn chỉnh** | `examples/ea-wizard-macd-sar-eurusd-h1-portfolio/` — turnaround 4 tiếng ở chế độ enterprise |
| **Test gate** | 234 test pass qua Phase 0/A/B/C/D/E |

### Bắt đầu nhanh (5 phút)

```bash
git clone https://github.com/BuildMqlCodekit-01/vibecodekit-mql5-ea
cd vibecodekit-mql5-ea
./scripts/setup-wine-metaeditor.sh        # chỉ Linux, ~3 phút
python -m venv .venv && source .venv/bin/activate
pip install -e .

python -m vibecodekit_mql5.doctor         # health check môi trường
python -m vibecodekit_mql5.build stdlib --name FirstEA --symbol EURUSD --tf H1
python -m vibecodekit_mql5.lint    FirstEA.mq5
python -m vibecodekit_mql5.compile FirstEA.mq5
```

Hướng dẫn chi tiết:
- Người mới — [docs/USAGE-vi.md](docs/USAGE-vi.md)
- Team dev + worked example — [examples/ea-wizard-macd-sar-eurusd-h1-portfolio/README.md](examples/ea-wizard-macd-sar-eurusd-h1-portfolio/README.md)
- Tích hợp IDE / CLI — [docs/ENV-SETUP-vi.md](docs/ENV-SETUP-vi.md)

### Lịch sử các phase

| Phase | Tag | Chủ đề | Điểm nhấn |
|-------|-----|--------|----------|
| 0 | `v0.0.1` | Bootstrap | Wine 8.0.2 + MetaEditor headless + Xvfb + CI |
| A | `v0.1.0` | Nền tảng | `CPipNormalizer`, `CRiskGuard`, `CMagicRegistry`, 8 AP nghiêm trọng, 3 scaffold stdlib |
| B | `v0.2.0` | Test & validation | Driver Strategy Tester, walk-forward, Monte-Carlo, multi-broker, Trader-17 |
| C | `v0.3.0` | Phương pháp luận | 6 RRI persona × 25 câu × 3 mode, workflow 8 bước, ma trận 64 ô, orchestrator 7 lớp |
| D | `v0.5.0` | Công nghệ 2024-2025 | ONNX runtime 1.14, HFT async, Algo Forge, LLM bridge (3 pattern), Cloud Network optimize, method-hiding linter |
| **E** | **`v1.0.0`** | **Polish & ship** | **28 tài liệu tham khảo, 3 MCP server, `/mql5-canary`, worked example 4 tiếng** |

### Anti-pattern kit từ chối ship

Kit này KHÔNG kế thừa các điểm nóng từ `vibecodekit-handwritten` (VCK-HU):

- `query_loop.py`, `tool_executor.py`, `intent_router.py`, `pipeline_router.py` — router chết, god module
- Master `/mql5` entrypoint một prompt — mỗi command đứng độc lập
- LLM bịa kết quả test — mọi tuyên bố "đã pass" phải truy ngược về XML report của Strategy Tester
- `OrderSend` không qua `CPipNormalizer` aware-MarketInfo — bất đối xứng digits/point gây sai pip ở JPY/XAU
- ONNX inference chưa validate trên Strategy Tester thật (bắt bởi AP-19)
- `OrderSendAsync` không có handler `OnTradeTransaction` (bắt bởi AP-18)
- `WebRequest` gọi trong `OnTick` (bắt bởi AP-17)
- Method-hiding trên subclass `CExpert` không có `using BaseClass::method;` (bắt từ build MetaEditor ≥ 5260)

---

## License

[MIT](LICENSE)
