# Test acceptance protocol and deterministic classification

## Data
Use `03_CASEBOOK_CANDIDATE_v1.csv` as source of the original 30; preserve every ID and original JSON input/output. `03_CASEBOOK_CANDIDATE_v2.csv` contains the v2 additions, not a replacement that permits reinterpreting v1. `03_SUPPLEMENTAL_V2_ENVELOPES.jsonl` is the authoritative serialized-envelope fixture input for parser/shape cases. Duplicate-key raw strings must be tested without dictionary decoding first.

## Contract specifics
The logical evaluator returns `ALLOW`, `BLOCK`, or `INVALID_INPUT` only. All fields are present in JSON and `reasons`/`warnings` are unique sorted arrays. Structurally malformed unrelated rows invalidate the entire request and suppress business warnings. Valid but irrelevant results get `UNRELATED_CHECK:<id>` warnings. Duplicate observations always invalidate, including identical duplicates, conflicting values and reversed order. Human `REQUEST EVIDENCE / DEFER RELEASE` is an educational action, not a machine enum.

## Expected experiment (predictions, NOT evidence)
- Weak suite selection from source: C1, C4, C5, C6, C7; baseline should pass.
- M1: expected weak pass, independent specific failures (as pinned CSV); warm-up only.
- M6: expected weak pass and strong failure C8.
- M8: expected weak pass, strong failure V6c, V6c2, with additional v2/supplement tests V6c3, S-MULTI and S-M8-REVERSE. Source classification must remain accurate.
- Other mutants M2/M3/M4/M5/M7 follow exact mechanism and case expectations in source oracle. Never invent extra kills or change predicted IDs to match observations.

## Terminal exit state
Baseline suite: rc 0, expected tests collected, no unexpected errors. Mutant `KILLED` only for rc 1 when all failures are assertions on the declared comparison, *and* failed ID set equals frozen prediction. rc 0 = `SURVIVED`; rc 2–5, no tests collected, crash, timeout, nonassertion errors = `HARNESS_ERROR`. Assertion failures with different IDs = `DISCREPANCY`, never auto-kill.

## Evidence package minimum
Immutable hashes for baseline, each mutant, fixtures, both test suites, exact command and environment, Python/pytest versions, test collection count, timestamp UTC, stdout/stderr, return code, case-to-node mapping, expected vs observed JSON and failure set. Report before/after correction changes; do not rewrite a pre-run oracle after execution.

## Acceptance for G2a
M8 candidate accepted for final educational choice only after observed and independently replayed weak-green and correct strong-red, including a demonstrable `ALLOW` misclassification for FAILED then PASSED duplicate case. Contradictory results are an engineering finding, not permission to publish anyway. M6 fallback requires its own controlled run and owner/editorial decision.
