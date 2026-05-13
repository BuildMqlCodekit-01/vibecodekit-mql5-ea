"""Phase A — compile log parser unit tests (3 tests).

These exercise `vibecodekit_mql5.compile.parse_log` against representative
MetaEditor output without spawning Wine. The e2e tests cover real
MetaEditor invocations.
"""
from __future__ import annotations

from vibecodekit_mql5.compile import parse_log


SUCCESS_LOG = """\

Z:\\demo.mq5 : information: compiling Z:\\demo.mq5
 : information: generating code
 : information: generating code 100%
 : information: code generated
Result: 0 errors, 0 warnings, 412 ms elapsed, cpu='X64 Regular'
"""

ERROR_LOG = """\
Z:\\bad.mq5(11,17) : error 256: undeclared identifier 'wat'
Z:\\bad.mq5(12,1) : error 149: ';' - unexpected token
Result: 2 errors, 0 warnings
"""

WARNING_LOG = """\
Z:\\warn.mq5(11,11) : warning 68: version '0.1.0' is incompatible with MQL5 Market
 : information: code generated
Result: 0 errors, 1 warnings, 401 ms elapsed, cpu='X64 Regular'
"""


def test_parse_log_success():
    r = parse_log(SUCCESS_LOG)
    assert r.success is True
    assert r.errors == [] and r.warnings == []


def test_parse_log_error():
    r = parse_log(ERROR_LOG)
    assert r.success is False
    assert len(r.errors) == 2
    assert "undeclared identifier" in r.errors[0]


def test_parse_log_warning_only():
    r = parse_log(WARNING_LOG)
    assert r.success is True
    assert len(r.warnings) == 1
    assert "version" in r.warnings[0]


# Regression: previously `"0 error" in low` substring-matched into "10 errors".
TEN_ERRORS_LOG = """\
Z:\\bulk.mq5(11,17) : error 256: undeclared identifier 'a'
Z:\\bulk.mq5(12,17) : error 256: undeclared identifier 'b'
Result: 10 errors, 0 warnings
"""

HUNDRED_ERRORS_LOG = """\
Z:\\worse.mq5(1,1) : error 1: bad
Result: 100 errors, 0 warnings
"""


def test_parse_log_ten_errors_is_failure():
    """Regression for substring-match bug: `Result: 10 errors` must fail."""
    r = parse_log(TEN_ERRORS_LOG)
    assert r.success is False


def test_parse_log_hundred_errors_is_failure():
    """Regression: `Result: 100 errors` must fail, not pass."""
    r = parse_log(HUNDRED_ERRORS_LOG)
    assert r.success is False
