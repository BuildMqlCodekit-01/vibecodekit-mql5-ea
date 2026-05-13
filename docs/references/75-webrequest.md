---
id: 75-webrequest
title: WebRequest patterns
tags: [webrequest, http]
applicable_phase: D
---

# WebRequest patterns

`WebRequest` is blocking; never call it inside `OnTick`
(AP-17).  Move it to `OnTimer` or a worker thread (build 3500+).
Whitelist the host in *Tools → Options → Expert Advisors → Allow
WebRequest for listed URL*.  Treat the API key as a secret: read it
from `TerminalInfoString(TERMINAL_DATA_PATH)` + a config file, do not
hard-code.
