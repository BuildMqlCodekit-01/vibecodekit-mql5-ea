"""Phase A top-level acceptance gate.

This module re-exports the 3 e2e tests + 25 unit tests so that a single
``pytest tests/gates/phase-A/test_phase_a_acceptance.py`` runs the full gate.

Individual test modules:
    test_e2e.py                 3 e2e gates
    test_lint_detectors.py      8 lint unit
    test_build_scaffolds.py     4 scaffold unit
    test_compile_log_parser.py  3 compile-log unit
    test_pip_normalize_refactor.py  5 refactor unit
    test_pipnorm_unit.py        5 CPipNormalizer unit
"""
from tests.gates.phase_A.test_e2e import *                        # noqa: F401,F403
from tests.gates.phase_A.test_lint_detectors import *             # noqa: F401,F403
from tests.gates.phase_A.test_build_scaffolds import *            # noqa: F401,F403
from tests.gates.phase_A.test_compile_log_parser import *         # noqa: F401,F403
from tests.gates.phase_A.test_pip_normalize_refactor import *     # noqa: F401,F403
from tests.gates.phase_A.test_pipnorm_unit import *               # noqa: F401,F403
