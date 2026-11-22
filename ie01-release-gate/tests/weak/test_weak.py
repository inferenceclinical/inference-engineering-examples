"""DELIBERATELY WEAK suite (disclosed). Handwritten by Claude Code from five casebook rows (C1, C4, C5, C6, C7).

Weakness by design: only five scenarios, no duplicates, no unrelated rows, no non-PASSED statuses other than
FAILED, and each test asserts the `decision` string only, never `reasons` or `warnings`.
"""
from ie01_gate import evaluate_release

ROWS_OK = [{"id": "unit", "status": "PASSED"}, {"id": "integration", "status": "PASSED"}]


def test_c1():
    assert evaluate_release(["unit", "integration"], ROWS_OK, "alice", "bob")["decision"] == "ALLOW"


def test_c4():
    rows = [{"id": "unit", "status": "PASSED"}, {"id": "integration", "status": "FAILED"}]
    assert evaluate_release(["unit", "integration"], rows, "alice", "bob")["decision"] == "BLOCK"


def test_c5():
    assert evaluate_release(["unit", "integration"], ROWS_OK, "alice", None)["decision"] == "BLOCK"


def test_c6():
    assert evaluate_release([], ROWS_OK, "alice", "bob")["decision"] == "INVALID_INPUT"


def test_c7():
    assert evaluate_release(["unit", "integration"], ROWS_OK, "alice", "alice")["decision"] == "BLOCK"
