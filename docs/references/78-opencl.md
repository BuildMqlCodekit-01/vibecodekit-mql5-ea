---
id: 78-opencl
title: OpenCL (GPU compute)
tags: [opencl, gpu]
applicable_phase: D
---

# OpenCL (GPU compute)

Build 3300+ exposes OpenCL via `CLContextCreate`,
`CLProgramCreate`, `CLKernelCreate`.  Use for neural-net training when
matrix/vector hit a wall; inference stays on CPU.
