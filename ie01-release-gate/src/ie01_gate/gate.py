"""IE01 reference release-evidence gate (synthetic teaching lab; not a real release authority).

Implements 02_NORMATIVE_POLICY_CONTRACT.md (proposed; IET named sign-off pending).
Pure function: no I/O, no coercion, trimming or normalisation of identifiers.
"""
import re

ID_PATTERN = re.compile(r"[a-z][a-z0-9_-]*", re.ASCII)  # always used with fullmatch
KNOWN_STATUSES = frozenset({"PASSED", "FAILED", "RUNNING", "SKIPPED", "CANCELLED"})
ENVELOPE_KEYS = ("required_checks", "results", "proposer", "reviewer")
_MISSING = object()  # an envelope key that was absent: reported as INPUT_SHAPE, never inspected


def _is_str(value):
    return type(value) is str  # JSON string only: bool, int, None and str subclasses are rejected


def _valid_id(value):
    return _is_str(value) and ID_PATTERN.fullmatch(value) is not None


def _evaluation(decision, reasons, warnings):
    return {"decision": decision, "reasons": sorted(set(reasons)), "warnings": sorted(set(warnings))}


def _evaluate(required_checks, results, proposer, reviewer, shape_error):
    errors = set()
    if shape_error:
        errors.add("INPUT_SHAPE")

    # 1. Structural facts, all inspected (no fail-fast); unsafe sub-containers skipped after their own error.
    if required_checks is not _MISSING:
        if type(required_checks) is not list:
            errors.add("CONFIG_TYPE")
        elif not required_checks:
            errors.add("CONFIG_EMPTY")
        else:
            seen_required = set()
            for item in required_checks:
                if not _valid_id(item):
                    errors.add("CONFIG_INVALID_ID")
                    continue
                if item in seen_required:
                    errors.add("CONFIG_DUPLICATE_ID")
                seen_required.add(item)

    valid_rows = []  # (id, status) in array order, only rows whose id and status are both well typed
    if results is not _MISSING:
        if type(results) is not list:
            errors.add("EVIDENCE_TYPE")
        else:
            seen_observed = set()
            for row in results:
                if type(row) is not dict or set(row) != {"id", "status"}:
                    errors.add("EVIDENCE_TYPE")  # wrong row shape: its id never enters duplicate detection
                    continue
                row_id, status = row["id"], row["status"]
                id_ok = _valid_id(row_id)
                if not id_ok:
                    errors.add("EVIDENCE_INVALID_ID")
                if not _is_str(status):
                    errors.add("EVIDENCE_STATUS_TYPE")
                if id_ok:
                    if row_id in seen_observed:
                        errors.add("EVIDENCE_DUPLICATE_ID")
                    seen_observed.add(row_id)
                    if _is_str(status):
                        valid_rows.append((row_id, status))

    if proposer is not _MISSING and not _is_str(proposer):
        errors.add("PROPOSER_TYPE")
    if reviewer is not _MISSING and reviewer is not None and not _is_str(reviewer):
        errors.add("REVIEWER_TYPE")

    # 2. Any structural error: INVALID_INPUT with structural codes only; business reasons and warnings suppressed.
    if errors:
        return _evaluation("INVALID_INPUT", errors, ())

    # 3. Business evaluation on structurally valid input.
    observed = {}
    for row_id, status in valid_rows:
        observed[row_id] = status  # distinct ids here (duplicates were rejected above)

    reasons, warnings = set(), set()
    required = list(required_checks)
    for check_id in required:
        if check_id not in observed:
            reasons.add(f"REQUIRED_MISSING:{check_id}")
            continue
        status = observed[check_id]
        if status == "PASSED":
            continue
        if status in KNOWN_STATUSES:
            reasons.add(f"REQUIRED_NOT_PASSED:{check_id}:{status}")
        else:
            reasons.add(f"REQUIRED_UNKNOWN_STATUS:{check_id}")
    required_set = set(required)
    for row_id in observed:
        if row_id not in required_set:
            warnings.add(f"UNRELATED_CHECK:{row_id}")

    # 4. Roles. String comparison only: it does not establish identity or review authority.
    if proposer.strip() == "":
        reasons.add("PROPOSER_BLANK")
    if reviewer is None:
        reasons.add("REVIEWER_ABSENT")
    elif reviewer.strip() == "":
        reasons.add("REVIEWER_BLANK")
    elif reviewer == proposer:
        reasons.add("SELF_REVIEW")

    return _evaluation("BLOCK" if reasons else "ALLOW", reasons, warnings)


def evaluate_release(required_checks, results, proposer, reviewer):
    """Evaluate already-decoded inputs. Returns {"decision", "reasons", "warnings"}.

    Limitation: a decoded Python mapping cannot reveal JSON members lost to duplicate keys upstream;
    use ie01_gate.parser.parse_strict_json on raw text for that guarantee.
    """
    return _evaluate(required_checks, results, proposer, reviewer, shape_error=False)


def evaluate_envelope(envelope):
    """Evaluate a decoded JSON envelope that must be an object with exactly the four contract keys."""
    if type(envelope) is not dict:
        return _evaluation("INVALID_INPUT", ["INPUT_SHAPE"], ())
    shape_error = set(envelope) != set(ENVELOPE_KEYS)
    values = [envelope.get(key, _MISSING) for key in ENVELOPE_KEYS]
    return _evaluate(*values, shape_error=shape_error)
