---
id: 70-algo-forge
title: Algo Forge (build 5100+ Git platform)
tags: [forge, git]
applicable_phase: D
---

# Algo Forge (build 5100+ Git platform)

MetaQuotes shipped a built-in Git host (Algo Forge) in build
5100+ at `forge.mql5.io`.  The kit wraps it via
`scripts/vibecodekit_mql5/forge_init.py` + `forge_pr.py` and the
`algo-forge-bridge` MCP server.  Authentication uses an API token
saved as `FORGE_API_TOKEN`.
