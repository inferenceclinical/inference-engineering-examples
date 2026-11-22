"""EXTRAS (informational, never gates a mutant verdict): contract details beyond the casebook. See prerun/extras_catalogue.md."""
import copy
import json
import os
import pathlib
import subprocess
import sys

import ie01_gate
from ie01_gate import evaluate_envelope, evaluate_release

RAW = pathlib.Path(__file__).resolve().parents[2] / "fixtures/raw_parser"
REQ = ["unit", "integration"]
OK = [{"id": "unit", "status": "PASSED"}, {"id": "integration", "status": "PASSED"}]


def ev(decision, reasons=(), warnings=()):
    return {"decision": decision, "reasons": list(reasons), "warnings": list(warnings)}


def test_e01_missing_top_level_key():
    assert evaluate_envelope({"required_checks": REQ, "results": OK, "proposer": "alice"}) == ev("INVALID_INPUT", ["INPUT_SHAPE"])


def test_e02_top_level_array():
    assert evaluate_envelope([REQ, OK, "alice", "bob"]) == ev("INVALID_INPUT", ["INPUT_SHAPE"])


def test_e03_unrelated_id_duplicated():
    rows = OK + [{"id": "e2e", "status": "PASSED"}, {"id": "e2e", "status": "PASSED"}]
    assert evaluate_release(REQ, rows, "alice", "bob") == ev("INVALID_INPUT", ["EVIDENCE_DUPLICATE_ID"])


def test_e04_missing_key_plus_independent_type_error():
    assert evaluate_envelope({"required_checks": REQ, "results": OK, "proposer": None}) == ev("INVALID_INPUT", ["INPUT_SHAPE", "PROPOSER_TYPE"])


def test_e05_multiple_business_reasons_sorted():
    assert evaluate_release(REQ, OK[:1], "alice", None) == ev("BLOCK", ["REQUIRED_MISSING:integration", "REVIEWER_ABSENT"])


def test_e06_warnings_sorted():
    rows = OK + [{"id": "e2e", "status": "PASSED"}, {"id": "docs", "status": "FAILED"}]
    assert evaluate_release(REQ, rows, "alice", "bob") == ev("ALLOW", [], ["UNRELATED_CHECK:docs", "UNRELATED_CHECK:e2e"])


def test_e07_both_blank_no_self_review():
    assert evaluate_release(REQ, OK, "  ", "  ") == ev("BLOCK", ["PROPOSER_BLANK", "REVIEWER_BLANK"])


def test_e08_boolean_status():
    assert evaluate_release(REQ, [OK[0], {"id": "integration", "status": True}], "alice", "bob") == ev("INVALID_INPUT", ["EVIDENCE_STATUS_TYPE"])


def test_e09_reviewer_false():
    assert evaluate_release(REQ, OK, "alice", False) == ev("INVALID_INPUT", ["REVIEWER_TYPE"])


def test_e10_non_ascii_required_id():
    assert evaluate_release(["unïit", "integration"], OK, "alice", "bob") == ev("INVALID_INPUT", ["CONFIG_INVALID_ID"])


def test_e11_row_is_string():
    assert evaluate_release(REQ, OK + ["e2e"], "alice", "bob") == ev("INVALID_INPUT", ["EVIDENCE_TYPE"])


def test_e12_required_contains_null():
    assert evaluate_release([None, "unit"], OK, "alice", "bob") == ev("INVALID_INPUT", ["CONFIG_INVALID_ID"])


def test_e13_evaluation_shape():
    for args in [(REQ, OK, "alice", "bob"), ([], OK, "alice", None), (REQ, OK, "alice", "alice")]:
        out = evaluate_release(*args)
        assert list(out) == ["decision", "reasons", "warnings"]
        assert isinstance(out["reasons"], list) and isinstance(out["warnings"], list)
        assert out["reasons"] == sorted(set(out["reasons"])) and out["warnings"] == sorted(set(out["warnings"]))


def test_e14_permutation_invariance():
    a = [{"id": "unit", "status": "PASSED"}, {"id": "e2e", "status": "PASSED"}]
    assert evaluate_release(REQ, a, "alice", "bob") == evaluate_release(list(reversed(REQ)), list(reversed(a)), "alice", "bob")


def test_e15_inputs_not_mutated():
    req, rows = copy.deepcopy(REQ), copy.deepcopy(OK)
    evaluate_release(req, rows, "alice", "bob")
    assert (req, rows) == (REQ, OK)


def test_e16_no_decide_release_alias():
    assert not hasattr(ie01_gate, "decide_release")


def test_e17_duplicate_with_bad_status_reports_both():
    rows = [{"id": "unit", "status": 5}, {"id": "unit", "status": "PASSED"}, OK[1]]
    assert evaluate_release(REQ, rows, "alice", "bob") == ev("INVALID_INPUT", ["EVIDENCE_DUPLICATE_ID", "EVIDENCE_STATUS_TYPE"])


def _cli(name):
    return subprocess.run([sys.executable, "-m", "ie01_gate", str(RAW / name)], capture_output=True, text=True, env=os.environ.copy(), timeout=30)


def test_e18_cli_ok():
    p = _cli("R-OK-C1.json")
    assert (p.returncode, json.loads(p.stdout), p.stderr) == (0, ev("ALLOW"), "")


def test_e19_cli_parser_error():
    p = _cli("R-DUP-TOP-RESULTS.json")
    assert p.returncode == 2 and p.stdout == "" and p.stderr.startswith("DuplicateKeyError: DUPLICATE_KEY")
