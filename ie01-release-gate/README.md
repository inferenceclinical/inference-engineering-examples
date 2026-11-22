# Lesson 1: The tests pass. Should the release go ahead?

Code for an Inference Public practical lesson.

**Do the lesson first.** It asks you to make two predictions before you see any results. This folder contains the answers.

## Start here
- **Inference Public:** [inferencepublic.co.uk](https://inferencepublic.co.uk/)
- **The lesson:** [The tests pass. Should the release go ahead?](https://inferencepublic.co.uk/learn/inference-engineering/green-tests-public-service-release/)
- **Printable prediction sheet:** [inferencepublic.co.uk/…/green-tests-prediction-sheet/](https://inferencepublic.co.uk/learn/inference-engineering/green-tests-prediction-sheet/)
- **Background reading:** [Verifying AI-generated code and tests](https://inferencepublic.co.uk/insights/verifying-ai-generated-code/)
- **More lessons:** [Inference engineering lessons](https://inferencepublic.co.uk/learn/inference-engineering/)

## What is here
| Path | What it is |
|---|---|
| `src/ie01_gate/` | The reference release gate: `evaluate_release(required_checks, results, proposer, reviewer)`, a strict JSON parser that rejects repeated keys, and a small CLI |
| `tests/weak/` | A **deliberately weak** suite: 5 handwritten tests that check only the decision word |
| `tests/strong/` | An **independent** suite written from the policy: 41 cases comparing the whole result, 5 raw-JSON parser tests and 3 fixture-provenance tests (49 in all) |
| `tests/extras/` | 19 extra contract tests, for information only |
| `mutants/M1.patch` … `M8.patch` | Eight deliberately broken versions of the gate, each a single small patch |
| `harness/run_experiment.py` | Runs the reference and every broken gate against both suites, and classifies each result against the predictions |
| `fixtures/` | The casebook of policy cases (CSV and JSONL) and raw-JSON test inputs |
| `prerun/` | **Predictions and file hashes, frozen before any code ran.** The harness refuses to run if any frozen file has changed |
| `results/` | The original results (first run, clean replay, harness controls), with local file paths removed |

`fixtures/source_pack/` keeps the original planning documents (policy contract, casebook, test protocol and prediction table) exactly as they were when the predictions were frozen. They are needed for the integrity check. They contain working notes about review steps that were still open at the time.

## Requirements
- **Tested on:** macOS 15 (Apple silicon) with Python 3.15.2 and pytest 9.2.0 (pinned by hash in `requirements-lock.txt`).
- **Should also work:** Linux with Python 3.10 or later. The harness uses the standard `patch` command.
- **Not tested:** Windows.
- **No network after installation,** no cloud account and no credentials.

## Run it
```sh
git clone https://github.com/inferenceclinical/inference-engineering-examples.git
cd inference-engineering-examples/ie01-release-gate
python3 -m venv .venv
.venv/bin/pip install --require-hashes -r requirements-lock.txt
```
If `python3` is older than 3.10, use a newer interpreter, for example `python3.12 -m venv .venv`.

### 1. Check the reference gate against both suites
```sh
PYTHONPATH=src .venv/bin/python -m pytest tests/weak -q -p no:cacheprovider
PYTHONPATH=src .venv/bin/python -m pytest tests/strong -q -p no:cacheprovider
```
**Expected:** `5 passed`, then `49 passed`.

### 2. Run the whole experiment
```sh
.venv/bin/python harness/run_experiment.py --label my-run
```
It prints one line per gate and suite (27 lines).

**The lines that matter for the lesson:**
```
BASELINE weak   rc=0 collected=5 failed=- -> BASELINE_PASS
BASELINE strong rc=0 collected=49 failed=- -> BASELINE_PASS
M8       weak   rc=0 collected=5 failed=- -> SURVIVED
M8       strong rc=1 collected=49 failed=S-M8-REVERSE;S-MULTI;V6c;V6c2;V6c3 -> KILLED
```

**How to read them:**
- **`SURVIVED`** on the weak suite means the weak tests did not notice the broken gate.
- **`KILLED`** means the independent tests failed on exactly the cases predicted in `prerun/frozen_predictions.csv`.

Your results are saved in `runs/<time>_my-run/`. Compare them with `results/first_run_mutation_results.csv`.

**Stop if you see:**
- `DISCREPANCY` or `HARNESS_ERROR` in any line
- `STOP: frozen files changed` at the start

Either means your copy differs from the published one.

### 3. Optional
```sh
.venv/bin/python harness/negative_controls.py      # three broken setups; each must show HARNESS_ERROR (OK)
PYTHONPATH=src .venv/bin/python -m ie01_gate fixtures/raw_parser/R-OK-C1.json             # prints an ALLOW result
PYTHONPATH=src .venv/bin/python -m ie01_gate fixtures/raw_parser/R-DUP-TOP-RESULTS.json   # exit 2: repeated JSON key rejected
```

## Try it yourself
To write a test straight from the policy, add one to `tests/strong/` that reports a check twice and expects `INVALID_INPUT` with `EVIDENCE_DUPLICATE_ID`. Then run it against the reference and against M8:
```sh
T=$(mktemp -d); cp -R src "$T/"; (cd "$T" && patch -p1 -i "$OLDPWD/mutants/M8.patch")
PYTHONPATH="$T/src" .venv/bin/python -m pytest tests/strong -q -p no:cacheprovider
```

## Limits
This is a teaching exercise:
- **Scenario:** fictional, with synthetic data.
- **What it proves:** nothing about legal compliance, real identities, review authority, recovery or any real service.
- **Who wrote the tests:** the "independent" suite was derived from the written policy, separately from the gate's code. It was not written by a different organisation.

## Licence
MIT. See [`../LICENSE`](../LICENSE).
