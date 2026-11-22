"""Harness negative controls (run after the frozen experiment; they never touch predictions or verdicts of M1-M8).

NC-EMPTY: suite with no tests (pytest rc 5)            -> must classify HARNESS_ERROR, never KILLED
NC-SYNTAX: implementation that cannot be imported (rc 2) -> HARNESS_ERROR
NC-CRASH: implementation raising RuntimeError (rc 1, non-assertion failures) -> HARNESS_ERROR
"""
import csv
import datetime
import os
import pathlib
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import run_experiment as rx  # noqa: E402

stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
run_dir = rx.ROOT / "runs" / f"{stamp}_negative-controls"
(run_dir / "raw").mkdir(parents=True)
work = pathlib.Path(os.environ.get("TMPDIR", "/tmp")) / f"ie01_nc_{stamp}"
rows = []
try:
    empty_suite = work / "empty_suite"
    empty_suite.mkdir(parents=True)
    rx.SUITES["empty"] = (str(empty_suite), 49)
    base = rx.build_impl("BASELINE", work)
    res = rx.run_suite(base, "NC-EMPTY", "empty", run_dir)
    rows.append(("NC-EMPTY", "empty suite dir", res, rx.classify(res, {"V6c"}, 49, True)))

    for name, mutate in [("NC-SYNTAX", lambda s: s.replace("def evaluate_release(", "def evaluate_release((", 1)),
                         ("NC-CRASH", lambda s: s.replace('    """Evaluate already-decoded inputs.', '    raise RuntimeError("control crash")\n    """Evaluate already-decoded inputs.', 1))]:
        root = work / name
        shutil.copytree(rx.ROOT / "src", root / "src")
        gate = root / "src/ie01_gate/gate.py"
        gate.write_text(mutate(gate.read_text()))
        res = rx.run_suite(root, name, "strong", run_dir)
        rows.append((name, "strong suite", res, rx.classify(res, {"V6c"}, 49, True)))
finally:
    shutil.rmtree(work, ignore_errors=True)

with open(run_dir / "negative_controls.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["control", "target", "rc", "collected", "non_assertion_failures_count", "classification", "expected", "ok"])
    for name, target, res, verdict in rows:
        ok = verdict.startswith("HARNESS_ERROR")
        w.writerow([name, target, res["rc"], res["collected"], len(res["non_assertion"]), verdict, "HARNESS_ERROR", ok])
        print(f"{name:10} rc={res['rc']} collected={res['collected']} non-assertion={len(res['non_assertion'])} -> {verdict} ({'OK' if ok else 'UNEXPECTED'})")
print("run dir:", run_dir.relative_to(rx.ROOT))
