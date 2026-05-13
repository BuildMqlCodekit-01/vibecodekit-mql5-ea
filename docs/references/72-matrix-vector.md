---
id: 72-matrix-vector
title: Matrix / vector first-class types
tags: [matrix, vector, blas]
applicable_phase: D
---

# Matrix / vector first-class types

Build 3300+ added `matrix` and `vector` as first-class types
with BLAS-backed operations: `MatMul`, `Inv`, `Det`, eigen
decomposition, etc.  Use them for portfolio math (covariance,
optimisation) instead of hand-rolled arrays.
