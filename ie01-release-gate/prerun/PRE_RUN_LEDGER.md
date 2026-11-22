# IE01 pre-run expectation ledger (frozen before any implementation or test exists)

Written by Claude Code on 22 November 2026, in isolated private lab `~/inferencepublic-recon/ie01-lab` (local git, no remote).
Owner authorisation exercised: "Yes, isolated local lab", plus a pinned pytest installed into the lab venv (owner answer, 22 November 2026).
**IET named technical sign-off is not evidenced. This ledger is a Claude Code engineering freeze, not a ratification.**

## What is frozen
- **Oracle:** `fixtures/source_pack/04_MUTATION_ORACLE_SPEC_PREDICTION_v2.csv`, copied verbatim (sha256 5221687…). It is never edited.
- **Machine-readable predictions:** `prerun/frozen_predictions.csv`. These are the oracle's weak and strong columns, with original and `predicted_supplemental_failures` merged into one strong set. The extras column is Claude Code's own derivation, used for information only.
- **Fixture hashes:** `prerun/fixture_hashes.csv`, all taken before code.
- **Source and test hashes:** captured in `prerun/FREEZE_RECORD.csv` after the code is written and **before the first execution** (git commit `freeze:`).

## Kill rule (from 04_MUTANT_KILL_RULE.md, applied mechanically by `harness/run_experiment.py`)
**Baseline condition:** the reference implementation must exit 0, with the expected collected count, on both the weak and strong suites. If it doesn't, the mutant is HARNESS_ERROR.

For each mutant and suite, after the baseline condition holds:

| Observed | Verdict |
|---|---|
| rc 0 | SURVIVED |
| rc 1, every failure an AssertionError, and the failed case-ID set equals the frozen set | KILLED |
| rc 1, but the failed set differs from the frozen set | DISCREPANCY |
| rc 2–5, collection error, crash, timeout, or any non-assertion failure | HARNESS_ERROR |

**Expected outcome on the weak suite:** for mutants whose weak prediction is "PASS", the expected outcome is SURVIVED, which is the deliberate weak-green.

The gating suites are weak and strong only. The extras suite is reported, but it never decides a verdict.

## Suites and case → pytest node mapping (naming fixed now)

**Weak suite** (`tests/weak/test_weak.py`):
- Five handwritten tests, C1, C4, C5, C6 and C7, which assert the `decision` field only. This is the deliberate weakness, disclosed.
- Node `tests/weak/test_weak.py::test_<ID lowercased>`, for example `::test_c1`.
- Expected collected: 5.

**Strong suite** (`tests/strong/`), written independently from the contract text:
- **Case tests:** `test_contract_cases.py::test_case[<CASE_ID>]`, one per case, comparing the **entire** Evaluation JSON object. It covers all 38 cases in v2 (the original 30 plus 8 supplemental) and the 3 proof fixtures, S-MULTI, S-M8-REVERSE and S-ID-VARIANT. That is 41 case tests.
- **Raw-JSON parser tests:** `test_raw_json_boundary.py::test_raw[<R-ID>]`, 5 tests. Predicted to pass under every mutant, because mutants change `gate.py` only.
- **Fixture provenance:** `test_fixture_provenance.py`, 3 tests:
  - the original 30 are byte-identical to the source and v2 is a superset
  - the JSONL and v2 CSV agree
  - an independent spec-oracle (`tests/strong/spec_oracle.py`, written separately from `src/`) reproduces every casebook expectation. This is a cross-check of the oracle, not of the SUT.
- **Expected collected:** 41 + 5 + 3 = 49.

**Extras suite** (`tests/extras/test_contract_extras.py::test_eNN_*`, informational): E01–E19, listed in `prerun/extras_catalogue.md`.

## Mutant mechanisms (each one patch against `src/ie01_gate/gate.py`; never combined)
| Mutant | Mechanism |
|---|---|
| M1 | A required check fails only if it is observed `FAILED`. Missing, RUNNING, SKIPPED, CANCELLED and unknown all count as passing. Structural validation is intact. |
| M2 | `RUNNING` is accepted as passing for required checks. |
| M3 | The REVIEWER_ABSENT, REVIEWER_BLANK and SELF_REVIEW checks are removed. The REVIEWER_TYPE and proposer checks are retained. |
| M4 | The `CONFIG_EMPTY` check is removed; everything else is intact. |
| M5 | Only the `SELF_REVIEW` equality check is removed. |
| M6 | `SKIPPED` is accepted as passing for required checks. |
| M7 | The `CONFIG_DUPLICATE_ID` check is removed, and required IDs are collapsed with `dict.fromkeys`. |
| M8 | The oracle-v2 pinned reading: per-row structural validation is intact, **only** the `EVIDENCE_DUPLICATE_ID` detection is removed, and the observed map is built after validation in array order, so later rows overwrite earlier ones. The review's variants b and c (a map built before validation) are **not** implemented. |

## Claude Code independent pre-run derivation (before code)
Claude Code derived each mutant from the contract text, and this derivation agrees with the oracle's strong set for every mutant:

- **M8:**
  - Forward V6c becomes BLOCK with `REQUIRED_NOT_PASSED:unit:FAILED`.
  - V6c2 becomes ALLOW.
  - **V6c3 and S-M8-REVERSE become an erroneous ALLOW**, because FAILED is overwritten by PASSED.
  - S-MULTI stays INVALID_INPUT but loses `EVIDENCE_DUPLICATE_ID`.
  - The weak cases have no duplicate rows, so the weak suite stays green.
- **M6:** only C8 becomes ALLOW.
- **Extras predictions:** listed in `extras_catalogue.md`.

## Gate 0 issue log (pre-run; no FDE/IET decision available; recorded rather than silently chosen)
- **I-01:** S-M8-REVERSE (contract) and V6c3 (v2 casebook and JSONL) have **identical inputs and expectations**. Both are kept as the oracle lists both, so M8's strong failure set counts the same scenario twice.
- **I-02:** S-ID-VARIANT is only partially specified ("unit and Unit in results"). Claude Code completed the envelope from C1. It needs IET confirmation.
- **I-03:** No raw-text parser fixtures were supplied, although the contract requires them. Claude Code derived R-DUP-TOP-RESULTS and R-DUP-ROW-STATUS from the contract text, and added three of its own: R-OK-C1 (positive control), R-NONSTANDARD-NAN and R-TRUNCATED.
- **I-04:** The contract is silent on non-standard JSON constants (NaN, Infinity), which Python's `json` accepts by default. The parser rejects them as `ParserError` (RFC 8259). This is a design decision that needs IET.
- **I-05:** A top-level JSON value that is not an object is treated as an Evaluation with `INPUT_SHAPE`, not as a parser error. The contract says only that the envelope "must be an object". This needs IET.
- **I-06:** "Blank / whitespace-only" is implemented as `str.strip() == ""`, Python's Unicode whitespace. The contract doesn't define the whitespace set; this needs IET.
- **I-07:** The oracle gives no predictions for tests beyond the case IDs. The extras suite is therefore informational and never gates a verdict.
- **I-08:** The oracle's hash columns read `NOT CREATED`, and `status` reads "SPECIFICATION PREDICTION; NOT EXECUTED". That is left unchanged. Actual hashes go in `FREEZE_RECORD.csv`, and the oracle is not renamed FROZEN (kill-rule design note).
- **I-09:** The pack doesn't pin a pytest version. pytest 9.2.0 is pinned by hash in `requirements-lock.txt`; Python is 3.15.2 (Homebrew).
- **I-10:** The FDE disposition says the pack does not authorise a lab until IET sign-off. The owner has now explicitly authorised the isolated local lab, so that sign-off gap is carried into the release gate, not closed.
