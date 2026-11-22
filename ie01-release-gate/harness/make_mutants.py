"""Generates mutants/Mk.patch (unified diff vs src/ie01_gate/gate.py). Each mutant = exactly the listed edits."""
import difflib
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = (ROOT / "src/ie01_gate/gate.py").read_text()

REQ_BLOCK = '''        if check_id not in observed:
            reasons.add(f"REQUIRED_MISSING:{check_id}")
            continue
        status = observed[check_id]
        if status == "PASSED":
            continue
        if status in KNOWN_STATUSES:
            reasons.add(f"REQUIRED_NOT_PASSED:{check_id}:{status}")
        else:
            reasons.add(f"REQUIRED_UNKNOWN_STATUS:{check_id}")
'''
REVIEWER_BLOCK = '''    if reviewer is None:
        reasons.add("REVIEWER_ABSENT")
    elif reviewer.strip() == "":
        reasons.add("REVIEWER_BLANK")
    elif reviewer == proposer:
        reasons.add("SELF_REVIEW")
'''
MUTANTS = {
    "M1": [(REQ_BLOCK, '''        if observed.get(check_id) == "FAILED":  # M1: only an observed FAILED blocks a required check
            reasons.add(f"REQUIRED_NOT_PASSED:{check_id}:FAILED")
''')],
    "M2": [('        if status == "PASSED":\n', '        if status in ("PASSED", "RUNNING"):  # M2: RUNNING treated as PASSED\n')],
    "M3": [(REVIEWER_BLOCK, "    pass  # M3: reviewer absence, blank and self-review checks bypassed (type check retained)\n")],
    "M4": [('        elif not required_checks:\n            errors.add("CONFIG_EMPTY")\n', "")],
    "M5": [('    elif reviewer == proposer:\n        reasons.add("SELF_REVIEW")\n', "")],
    "M6": [('        if status == "PASSED":\n', '        if status in ("PASSED", "SKIPPED"):  # M6: SKIPPED converted to passing evidence\n')],
    "M7": [('                if item in seen_required:\n                    errors.add("CONFIG_DUPLICATE_ID")\n', ""),
           ("    required = list(required_checks)\n", "    required = list(dict.fromkeys(required_checks))  # M7: duplicates silently collapsed\n")],
    "M8": [('                    if row_id in seen_observed:\n                        errors.add("EVIDENCE_DUPLICATE_ID")\n', ""),
           ("        observed[row_id] = status  # distinct ids here (duplicates were rejected above)\n",
            "        observed[row_id] = status  # M8: no duplicate detection, so later rows overwrite earlier ones\n")],
}

for name, edits in MUTANTS.items():
    text = SRC
    for old, new in edits:
        assert text.count(old) == 1, (name, old)
        text = text.replace(old, new)
    diff = difflib.unified_diff(SRC.splitlines(True), text.splitlines(True), "a/src/ie01_gate/gate.py", "b/src/ie01_gate/gate.py")
    (ROOT / f"mutants/{name}.patch").write_text("".join(diff))
    print(name, "edits", len(edits))
