# Proposed normative policy contract (IET sign-off pending)
**Scope:** deterministic synthetic release-evidence gate. Nothing here is a real council release authority.

## Function and JSON boundary
Logical function `evaluate_release(required_checks, results, proposer, reviewer) -> Evaluation` accepts exactly four arguments, represented in JSON with keys `required_checks`, `results`, `proposer`, `reviewer`. The top-level envelope must be an object with precisely those four keys; unknown or absent top-level keys yield `INPUT_SHAPE` if a JSON interface is implemented. Python API call may be bound by positional/keyword arguments but must preserve the same semantics. No silent string conversion, coercion, trimming or normalisation of identifiers.

- `required_checks`: JSON **array**, nonempty; each item is JSON string matching ASCII `[a-z][a-z0-9_-]*` against the *entire* string (`re.fullmatch`, not `re.match` or a permissive `$` anchor); no duplicate IDs.
- `results`: JSON **array** of JSON **objects**, each having **exactly** string `id` and `status` fields (no missing/extra fields). `id` uses the same full-string ASCII rule; repeated result IDs are invalid whether values agree or conflict. Preserve array order until duplicate checks finish. Do not use a dict to normalise first.
- `status`: JSON string. Supported statuses `PASSED`, `FAILED`, `RUNNING`, `SKIPPED`, `CANCELLED`. Unknown *string* on a required check produces `BLOCK` with `REQUIRED_UNKNOWN_STATUS:<id>`; unknown *string* on structurally valid unrelated result is warning-only `UNRELATED_CHECK:<id>`. `null`, number, list/object and absent status cause `INVALID_INPUT`; a row with absent `id` or `status` has `EVIDENCE_TYPE`, while a present non-string `status` has `EVIDENCE_STATUS_TYPE`.
- `proposer`: JSON string; blank/whitespace-only blocks. Non-string including null is `INVALID_INPUT` with `PROPOSER_TYPE`.
- `reviewer`: JSON string or null. Null means valid-but-absent => `BLOCK` / `REVIEWER_ABSENT`; blank/whitespace-only string => `BLOCK` / `REVIEWER_BLANK`; other non-string => `INVALID_INPUT` / `REVIEWER_TYPE`. Identical exact proposer and reviewer strings => `BLOCK` / `SELF_REVIEW`. Comparing strings does not validate identity or authority. Do not casefold/normalise for equality; `alice` and `Alice` are different in this lab (known limitation).
- `Evaluation` is JSON object exactly `{"decision":"ALLOW|BLOCK|INVALID_INPUT","reasons":["..."],"warnings":["..."]}`. `reasons` and `warnings` are arrays of unique, lexicographically sorted ASCII strings; empty arrays rather than null. No bare enum/string return is valid.

## Validation order and precedence
1. Validate *all independent structural/type facts* that are safe to inspect: container shapes, required identifiers, duplicate required IDs, every result row shape/ID/status type, duplicate observed IDs, proposer/reviewer types. Do not fail on first recoverable structural issue. For invalid subcontainers, record the container-level error and skip unsafe descent only for that subcontainer; still inspect other independent inputs. Duplicates are detected for otherwise syntactically valid ID strings even when some row has a malformed status; however malformed row *shape* (missing/extra keys) contributes `EVIDENCE_TYPE` only and its ID does not enter duplicate detection. For a complete two-key row, an ID of any non-string JSON type (including boolean) contributes `EVIDENCE_INVALID_ID`, and a non-string status contributes `EVIDENCE_STATUS_TYPE`.
2. If any structural error: **`INVALID_INPUT`**, sorted unique structural/type reason codes; **no business reasons, no unrelated warnings**. Thus C6/N12 suppress reviewer absence, and C6 has no UNRELATED warning even with valid observed rows.
3. Else evaluate all required evidence IDs: missing => `REQUIRED_MISSING:<id>`; observed `PASSED` => success; known other status => `REQUIRED_NOT_PASSED:<id>:<STATUS>`; unknown string => `REQUIRED_UNKNOWN_STATUS:<id>`. Every well-formed unrelated result yields warning `UNRELATED_CHECK:<id>` regardless of its string status, including unknown. Warnings never cause an ALLOW or repair a missing required result.
4. Add `PROPOSER_BLANK`, `REVIEWER_ABSENT`, `REVIEWER_BLANK`, `SELF_REVIEW` where applicable on structurally valid input, without double-reporting mutually exclusive reviewer defects (e.g. blank reviewer does not also create SELF_REVIEW). Any business reason => **BLOCK**; otherwise **ALLOW**. Sort/deduplicate reasons and warnings.
5. Arrays of input rows are order-insensitive for valid evidence; duplicated observed IDs are always invalid even if conflicting rows are reversed. Exact source set is frozen before any run.

## Structural reason code vocabulary
`INPUT_SHAPE` (missing/extra top-level fields), `CONFIG_TYPE`, `CONFIG_EMPTY`, `CONFIG_INVALID_ID` (including non-string items and booleans), `CONFIG_DUPLICATE_ID`, `EVIDENCE_TYPE` (not array, row not object, missing/extra row keys), `EVIDENCE_INVALID_ID`, `EVIDENCE_STATUS_TYPE`, `EVIDENCE_DUPLICATE_ID`, `PROPOSER_TYPE`, `REVIEWER_TYPE`. All are deterministic generic codes, not bound to array offsets; deduplicated and alphabetically sorted. Malformed unrelated rows invalidate complete input. If duplicated valid IDs also have bad status types, report both errors.

## Business reason and warning vocabulary
`REQUIRED_MISSING:<id>`, `REQUIRED_NOT_PASSED:<id>:<STATUS>`, `REQUIRED_UNKNOWN_STATUS:<id>`, `PROPOSER_BLANK`, `REVIEWER_ABSENT`, `REVIEWER_BLANK`, `SELF_REVIEW`; warning `UNRELATED_CHECK:<id>`. Dynamic IDs come only from validated ASCII identifiers. `INVALID_INPUT` suppresses *all* business codes/warnings. Reason sorting is exact lexical Unicode/codepoint order of ASCII strings.

## Complete original-fixture examples (exact source JSON values)
All data below comes from `04_CASEBOOK_VALIDATION.csv`, with proposed review outputs; no program executed.

**C6** input: `{"required_checks":[],"results":[{"id":"unit","status":"PASSED"},{"id":"integration","status":"PASSED"}],"proposer":"alice","reviewer":"bob"}`
output: `{"decision":"INVALID_INPUT","reasons":["CONFIG_EMPTY"],"warnings":[]}`.

**N12** input: `{"required_checks":[],"results":[{"id":"unit","status":"PASSED"},{"id":"integration","status":"PASSED"}],"proposer":"alice","reviewer":null}`
output: `{"decision":"INVALID_INPUT","reasons":["CONFIG_EMPTY"],"warnings":[]}` (not REVIEWER_ABSENT).

**N8** input: `{"required_checks":["unit","integration"],"results":[{"id":"unit","status":"PASSED"},{"id":"e2e","status":"PASSED"}],"proposer":"alice","reviewer":"bob"}`
output: `{"decision":"BLOCK","reasons":["REQUIRED_MISSING:integration"],"warnings":["UNRELATED_CHECK:e2e"]}`.

**V6c** input: `{"required_checks":["unit","integration"],"results":[{"id":"unit","status":"PASSED"},{"id":"unit","status":"FAILED"},{"id":"integration","status":"PASSED"}],"proposer":"alice","reviewer":"bob"}`
output: `{"decision":"INVALID_INPUT","reasons":["EVIDENCE_DUPLICATE_ID"],"warnings":[]}`.

**V6c2** input: `{"required_checks":["unit","integration"],"results":[{"id":"unit","status":"PASSED"},{"id":"unit","status":"PASSED"},{"id":"integration","status":"PASSED"}],"proposer":"alice","reviewer":"bob"}`
output: `{"decision":"INVALID_INPUT","reasons":["EVIDENCE_DUPLICATE_ID"],"warnings":[]}`.

**C8** input: `{"required_checks":["unit","integration"],"results":[{"id":"unit","status":"PASSED"},{"id":"integration","status":"SKIPPED"}],"proposer":"alice","reviewer":"bob"}`
output: `{"decision":"BLOCK","reasons":["REQUIRED_NOT_PASSED:integration:SKIPPED"],"warnings":[]}`.

## Supplementary proof inputs (not silently added to original 30)
**S-MULTI**: `required_checks=["unit","unit","BAD"]`; `results=[{"id":"unit","status":null},{"id":"unit","status":"PASSED"},{"id":"e2e"}]`; `proposer=null`, `reviewer=7`. Expected **INVALID_INPUT** with `reasons=["CONFIG_DUPLICATE_ID","CONFIG_INVALID_ID","EVIDENCE_DUPLICATE_ID","EVIDENCE_STATUS_TYPE","EVIDENCE_TYPE","PROPOSER_TYPE","REVIEWER_TYPE"]`, warnings `[]`.

**S-M8-REVERSE**: V6c results in reverse duplicate order (`unit FAILED`, then `unit PASSED`, then `integration PASSED`). Expected **INVALID_INPUT** / `["EVIDENCE_DUPLICATE_ID"]` / `[]`. An M8 overwrite-last mutant may incorrectly ALLOW here whereas forward V6c incorrectly BLOCKs. This is an *additional* required future proof fixture, distinct from the 30-source-case register.

**S-ID-VARIANT**: `unit` and `Unit` in results: second ID invalid (`EVIDENCE_INVALID_ID`), even though case variation might be accepted by other systems. Keep separate from the `alice`/`Alice` identity example N11.

## Evidence limitations
No source code, policy runtime, supplier queue, real tester identity, review mandate or assisted route has been executed or validated. Formal IET sign-off of this *proposed* contract remains pending.

## Contract v2 clarifications — proposed, awaiting named IET acceptance
- Function name is `evaluate_release`; reject undocumented `decide_release` alias until independently approved.
- `required_checks` must be a nonempty JSON array. All non-string identifiers (including booleans), trailing newlines, non-ASCII or otherwise invalid strings give `CONFIG_INVALID_ID`.
- `results` must be a JSON array of objects with exactly keys `id` and `status`. Invalid row shape contributes `EVIDENCE_TYPE` only (do not inspect that row for duplicates). Present non-string ID gives `EVIDENCE_INVALID_ID`; present non-string status gives `EVIDENCE_STATUS_TYPE`.
- A missing/extra top-level field contributes `INPUT_SHAPE`. Independent safely inspectable subfields may contribute other codes, and malformed subcontainers are skipped after reporting their container error.
- The JSON parser boundary MUST reject duplicate keys in the original JSON text before constructing the input object, or explicitly declare this an unresolved interface limitation that blocks JSON-interface release. The Python function cannot detect keys already overwritten by parsing.
- Input data types must follow JSON type rules; `bool` is not a valid string even if it is accepted by broad Python type checks.
- The original 30 fixtures are invariant; extra v2 cases are candidate contract tests, not executed evidence.

## Raw serialized JSON duplicate-key boundary — amendment candidate
Where IE01 accepts raw serialized JSON, it must parse with recursive duplicate-key detection and reject any object with repeated member names before conversion into a map/dictionary. This is a **transport/parser error**, not an `Evaluation` with a fabricated gate reason. Record parser error class and non-sensitive diagnostics. Add negative raw-text parser fixtures with duplicate top-level `results` keys and repeated row `status` keys. An already decoded Python mapping cannot reveal keys lost upstream; document that limitation.
