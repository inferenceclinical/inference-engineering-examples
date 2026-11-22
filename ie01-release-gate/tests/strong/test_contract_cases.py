"""INDEPENDENT STRONG suite: every casebook and proof case, comparing the ENTIRE Evaluation object."""
import pytest

from fixtures_loader import strong_cases
from ie01_gate import evaluate_envelope, evaluate_release

CASES = strong_cases()


@pytest.mark.parametrize("case_id,kind,payload,expected", CASES, ids=[c[0] for c in CASES])
def test_case(case_id, kind, payload, expected):
    observed = evaluate_release(*payload) if kind == "args" else evaluate_envelope(payload)
    assert observed == expected
