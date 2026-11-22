# Extras suite catalogue (informational; predictions frozen pre-run)
| ID | Test | Expected (reference) | Predicted failing mutants |
|---|---|---|---|
| E01 | missing top-level key `reviewer` | INVALID_INPUT [INPUT_SHAPE] | none |
| E02 | top-level JSON array | INVALID_INPUT [INPUT_SHAPE] | none |
| E03 | unrelated ID duplicated (`e2e` twice, valid) | INVALID_INPUT [EVIDENCE_DUPLICATE_ID] | M8 |
| E04 | missing key plus independent bad proposer type | INVALID_INPUT [INPUT_SHAPE, PROPOSER_TYPE] | none |
| E05 | missing integration plus reviewer null: reasons sorted | BLOCK [REQUIRED_MISSING:integration, REVIEWER_ABSENT] | M1, M3 |
| E06 | two unrelated checks: warnings sorted | ALLOW, warnings [UNRELATED_CHECK:docs, UNRELATED_CHECK:e2e] | none |
| E07 | proposer and reviewer both whitespace: no SELF_REVIEW | BLOCK [PROPOSER_BLANK, REVIEWER_BLANK] | M3 |
| E08 | boolean status | INVALID_INPUT [EVIDENCE_STATUS_TYPE] | none |
| E09 | reviewer `false` | INVALID_INPUT [REVIEWER_TYPE] | none |
| E10 | non-ASCII required ID `unït` | INVALID_INPUT [CONFIG_INVALID_ID] | none |
| E11 | result row is a string | INVALID_INPUT [EVIDENCE_TYPE] | none |
| E12 | required_checks contains null | INVALID_INPUT [CONFIG_INVALID_ID] | none |
| E13 | the Evaluation has exactly three keys, lists not null, for every casebook case | holds | none |
| E14 | permutation invariance on N8 rows | equal outputs | none |
| E15 | input objects are not mutated | holds | none |
| E16 | Python API rejects the alias `decide_release` (not exported) | holds | none |
| E17 | duplicate valid IDs where one row has an int status | INVALID_INPUT [EVIDENCE_DUPLICATE_ID, EVIDENCE_STATUS_TYPE] | M8 |
| E18 | CLI on R-OK-C1 | rc 0, stdout ALLOW JSON | none |
| E19 | CLI on R-DUP-TOP-RESULTS | rc 2, stderr names ParserError, no Evaluation on stdout | none |
