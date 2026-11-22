"""Independent re-statement of the written policy, used ONLY to cross-check casebook expectations.

Written separately from src/ (different structure: a list of rule functions) by the same author, so it is a
consistency check on the fixtures, not independent human verification.
"""
import re

_ID = re.compile(r"\A[a-z][a-z0-9_-]*\Z", re.ASCII)
_KNOWN = ("PASSED", "FAILED", "RUNNING", "SKIPPED", "CANCELLED")
_KEYS = ["proposer", "required_checks", "results", "reviewer"]


def _ok_id(v):
    return isinstance(v, str) and not isinstance(v, bool) and _ID.match(v) is not None and "\n" not in v


def spec(envelope):
    if not isinstance(envelope, dict):
        return {"decision": "INVALID_INPUT", "reasons": ["INPUT_SHAPE"], "warnings": []}
    s = []
    if sorted(envelope) != _KEYS:
        s.append("INPUT_SHAPE")
    rc = envelope.get("required_checks", ...)
    if rc is not ...:
        if not isinstance(rc, list):
            s.append("CONFIG_TYPE")
        elif len(rc) == 0:
            s.append("CONFIG_EMPTY")
        else:
            good = [x for x in rc if _ok_id(x)]
            if len(good) < len(rc):
                s.append("CONFIG_INVALID_ID")
            if len(good) != len(set(good)):
                s.append("CONFIG_DUPLICATE_ID")
    res = envelope.get("results", ...)
    pairs = []
    if res is not ...:
        if not isinstance(res, list):
            s.append("EVIDENCE_TYPE")
        else:
            ids = []
            for r in res:
                if not (isinstance(r, dict) and sorted(r) == ["id", "status"]):
                    s.append("EVIDENCE_TYPE")
                    continue
                if _ok_id(r["id"]):
                    ids.append(r["id"])
                else:
                    s.append("EVIDENCE_INVALID_ID")
                if not isinstance(r["status"], str):
                    s.append("EVIDENCE_STATUS_TYPE")
                elif _ok_id(r["id"]):
                    pairs.append((r["id"], r["status"]))
            if len(ids) != len(set(ids)):
                s.append("EVIDENCE_DUPLICATE_ID")
    p = envelope.get("proposer", ...)
    if p is not ... and not isinstance(p, str):
        s.append("PROPOSER_TYPE")
    v = envelope.get("reviewer", ...)
    if v is not ... and v is not None and not isinstance(v, str):
        s.append("REVIEWER_TYPE")
    if s:
        return {"decision": "INVALID_INPUT", "reasons": sorted(set(s)), "warnings": []}
    seen = dict(pairs)
    b = []
    for c in rc:
        st = seen.get(c)
        b += ([] if st == "PASSED" else [f"REQUIRED_MISSING:{c}"] if st is None
              else [f"REQUIRED_NOT_PASSED:{c}:{st}"] if st in _KNOWN else [f"REQUIRED_UNKNOWN_STATUS:{c}"])
    w = [f"UNRELATED_CHECK:{i}" for i in seen if i not in rc]
    if not p.strip():
        b.append("PROPOSER_BLANK")
    b += (["REVIEWER_ABSENT"] if v is None else ["REVIEWER_BLANK"] if not v.strip()
          else ["SELF_REVIEW"] if v == p else [])
    return {"decision": "BLOCK" if b else "ALLOW", "reasons": sorted(set(b)), "warnings": sorted(set(w))}
