"""Fixture provenance: the original 30 are unmodified; v2 additions agree across CSV and JSONL; spec cross-check."""
import hashlib

from fixtures_loader import ENVELOPES, V1, V2, csv_rows, jsonl, strong_cases, _strict
from spec_oracle import spec

ORIGINAL_SHA256 = "f0a8948df20288e072d24b458e0cde33640d38c2791f1b81f42a9b96f504af02"


def test_original_30_unmodified():
    assert hashlib.sha256(V1.read_bytes()).hexdigest() == ORIGINAL_SHA256
    v1, v2 = csv_rows(V1), csv_rows(V2)
    assert len(v1) == 30 and len(v2) == 38
    assert v2[:30] == v1


def test_v2_csv_and_jsonl_agree():
    v2 = {r["case_id"]: r for r in csv_rows(V2)}
    recs = jsonl(ENVELOPES)
    assert [r["case_id"] for r in recs] == [r["case_id"] for r in csv_rows(V2)][30:]
    for rec in recs:
        assert _strict(v2[rec["case_id"]]["expected_output_json"]) == rec["expected"]


def test_spec_oracle_reproduces_every_expectation():
    keys = ("required_checks", "results", "proposer", "reviewer")
    mismatches = []
    for cid, kind, payload, expected in strong_cases():
        envelope = dict(zip(keys, payload)) if kind == "args" else payload
        if spec(envelope) != expected:
            mismatches.append(cid)
    assert mismatches == []
