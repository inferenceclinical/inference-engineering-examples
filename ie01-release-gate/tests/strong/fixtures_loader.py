"""Loads fixtures exactly as supplied. JSON values in the casebook are decoded with the strict parser."""
import csv
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
FIX = ROOT / "fixtures"
V1 = FIX / "source_pack/03_CASEBOOK_CANDIDATE_v1.csv"
V2 = FIX / "source_pack/03_CASEBOOK_CANDIDATE_v2.csv"
ENVELOPES = FIX / "source_pack/03_SUPPLEMENTAL_V2_ENVELOPES.jsonl"
PROOF = FIX / "supplemental_proof.jsonl"
RAW = FIX / "raw_parser"


def _strict(text):
    def hook(pairs):
        keys = [k for k, _ in pairs]
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate key in fixture")
        return dict(pairs)
    return json.loads(text, object_pairs_hook=hook)


def csv_rows(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def jsonl(path):
    return [_strict(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def strong_cases():
    """[(case_id, kind, payload, expected)]: kind 'args' (four API args) or 'envelope' (decoded envelope)."""
    envelopes = {r["case_id"]: r for r in jsonl(ENVELOPES)}
    cases = []
    for row in csv_rows(V2):
        cid = row["case_id"]
        if cid in envelopes:  # the JSONL is the authoritative serialized input for the v2 additions
            cases.append((cid, "envelope", envelopes[cid]["input"], envelopes[cid]["expected"]))
        else:
            args = tuple(_strict(row[k]) for k in ("required_checks_json", "result_rows_json", "proposer_json", "reviewer_json"))
            cases.append((cid, "args", args, _strict(row["expected_output_json"])))
    for rec in jsonl(PROOF):
        cases.append((rec["case_id"], "envelope", rec["input"], rec["expected"]))
    return cases
