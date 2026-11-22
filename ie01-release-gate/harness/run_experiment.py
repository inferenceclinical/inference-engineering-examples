"""IE01 mutation experiment harness. Usage: python harness/run_experiment.py [--label NAME]

Verifies the pre-run freeze, then runs baseline and M1-M8 against the weak, strong and extras suites,
classifying each run mechanically by prerun/frozen_predictions.csv and the kill rule. It never edits predictions.
"""
import csv
import datetime
import hashlib
import json
import os
import pathlib
import platform
import re
import shutil
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
PY = sys.executable
SUITES = {"weak": ("tests/weak", 5), "strong": ("tests/strong", 49), "extras": ("tests/extras", 19)}
IMPLS = ["BASELINE", "M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8"]
TIMEOUT = 300


def sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def verify_freeze():
    rows = list(csv.DictReader(open(ROOT / "prerun/FREEZE_RECORD.csv")))
    bad = [r["path"] for r in rows if not (ROOT / r["path"]).exists() or sha(ROOT / r["path"]) != r["sha256"]]
    if bad:
        sys.exit(f"STOP: frozen files changed since freeze: {bad}")
    return {r["path"]: r["sha256"] for r in rows}


def predictions():
    out = {}
    for r in csv.DictReader(open(ROOT / "prerun/frozen_predictions.csv")):
        split = lambda s: set(filter(None, s.split(";")))
        out[r["mutant"]] = {"weak": split(r["weak_expected_failing"]), "strong": split(r["strong_expected_failing"]),
                            "extras": split(r["extras_expected_failing"])}
    return out


def case_id(nodeid):
    m = re.search(r"\[(.+)\]$", nodeid)
    if m:
        return m.group(1)
    name = nodeid.rsplit("::", 1)[-1]
    m = re.match(r"test_(c\d+)$", name)
    if m:
        return m.group(1).upper()
    m = re.match(r"test_(e\d+)_", name)
    return m.group(1).upper() if m else name


def build_impl(name, impls_dir):
    """Copy src/ to <impls_dir>/<name>/src and, for a mutant, apply exactly mutants/<name>.patch there."""
    root = impls_dir / name
    shutil.copytree(ROOT / "src", root / "src", ignore=shutil.ignore_patterns("__pycache__"))
    if name != "BASELINE":
        p = subprocess.run(["/usr/bin/patch", "-p1", "--no-backup-if-mismatch", "-i", str(ROOT / f"mutants/{name}.patch")],
                           cwd=root, capture_output=True, text=True)
        if p.returncode != 0:
            sys.exit(f"STOP: patch {name} failed: {p.stdout}{p.stderr}")
    return root


def run_suite(impl_root, impl, suite, run_dir):
    path, _ = SUITES[suite]
    report = run_dir / "raw" / f"{impl}_{suite}.json"
    env = {"PATH": "/usr/bin:/bin", "PYTHONPATH": f"{impl_root / 'src'}{os.pathsep}{ROOT / 'harness'}",
           "IE01_REPORT": str(report), "PYTHONDONTWRITEBYTECODE": "1", "PYTHONHASHSEED": "0"}
    cmd = [PY, "-m", "pytest", path, "-p", "ie01_report_plugin", "-p", "no:cacheprovider", "-q", "-rN"]
    t0 = time.monotonic()
    try:
        p = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True, timeout=TIMEOUT)
        rc, out, err = p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired as exc:
        rc, out, err = "TIMEOUT", exc.stdout or "", exc.stderr or ""
    dur = round(time.monotonic() - t0, 3)
    (run_dir / "raw" / f"{impl}_{suite}.stdout.txt").write_text(out if isinstance(out, str) else out.decode())
    (run_dir / "raw" / f"{impl}_{suite}.stderr.txt").write_text(err if isinstance(err, str) else err.decode())
    data = json.loads(report.read_text()) if report.exists() else {"collected": None, "results": []}
    failed = [r for r in data["results"] if r["outcome"] == "failed"]
    return {"cmd": " ".join(cmd), "env_PYTHONPATH": env["PYTHONPATH"], "rc": rc, "duration_s": dur,
            "collected": data["collected"], "failed_ids": sorted(case_id(r["nodeid"]) for r in failed),
            "failed_nodes": sorted(r["nodeid"] for r in failed),
            "non_assertion": sorted(f'{r["nodeid"]}:{r["when"]}:{r["exception"]}' for r in failed
                                    if r["when"] != "call" or r["exception"] != "AssertionError")}


def classify(res, expected_fail, expected_count, baseline_ok):
    if not baseline_ok:
        return "HARNESS_ERROR (baseline condition not met)"
    if res["rc"] == 0 and res["collected"] == expected_count:
        return "SURVIVED"
    if res["rc"] == 1 and res["collected"] == expected_count and not res["non_assertion"]:
        return "KILLED" if set(res["failed_ids"]) == expected_fail else "DISCREPANCY"
    return "HARNESS_ERROR"


def case_outputs(impl_root):
    code = ("import json,sys;sys.path[:0]=[sys.argv[1],sys.argv[2]];from fixtures_loader import strong_cases;"
            "from ie01_gate import evaluate_release,evaluate_envelope;"
            "print(json.dumps([{'case_id':c,'expected':e,'observed':(evaluate_release(*p) if k=='args' else evaluate_envelope(p))}"
            " for c,k,p,e in strong_cases()]))")
    p = subprocess.run([PY, "-I", "-c", code, str(impl_root / "src"), str(ROOT / "tests/strong")], capture_output=True, text=True)
    return json.loads(p.stdout)


def main():
    label = sys.argv[sys.argv.index("--label") + 1] if "--label" in sys.argv else "run"
    frozen = verify_freeze()
    preds = predictions()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = ROOT / "runs" / f"{stamp}_{label}"
    (run_dir / "raw").mkdir(parents=True)
    impls_dir = pathlib.Path(os.environ.get("TMPDIR", "/tmp")) / f"ie01_impls_{stamp}_{os.getpid()}"
    env_info = {"utc_start": stamp, "python": sys.version, "executable": PY, "platform": platform.platform(),
                "pytest": subprocess.run([PY, "-m", "pytest", "--version"], capture_output=True, text=True).stdout.strip(),
                "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip(),
                "git_dirty": subprocess.run(["git", "status", "--porcelain", "--", "src", "tests", "mutants", "harness", "fixtures", "prerun"],
                                            cwd=ROOT, capture_output=True, text=True).stdout.strip() or "clean",
                "frozen_files_verified": len(frozen)}
    rows, outputs, baseline_ok = [], {}, None
    try:
        for impl in IMPLS:
            root = build_impl(impl, impls_dir)
            gate_sha = sha(root / "src/ie01_gate/gate.py")
            outputs[impl] = case_outputs(root)
            for suite in SUITES:
                res = run_suite(root, impl, suite, run_dir)
                exp_count = SUITES[suite][1]
                if impl == "BASELINE":
                    ok = res["rc"] == 0 and res["collected"] == exp_count and not res["failed_ids"]
                    verdict = "BASELINE_PASS" if ok else "BASELINE_FAIL"
                    if suite in ("weak", "strong"):
                        baseline_ok = ok if baseline_ok is None else (baseline_ok and ok)
                    exp = set()
                else:
                    exp = preds[impl][suite]
                    verdict = classify(res, exp, exp_count, baseline_ok)
                    if suite == "extras":
                        verdict = "INFO_MATCHES_PREDICTION" if set(res["failed_ids"]) == exp and not res["non_assertion"] else "INFO_DIFFERS_FROM_PREDICTION"
                rows.append({"impl": impl, "suite": suite, "gate_py_sha256": gate_sha,
                             "patch_sha256": "" if impl == "BASELINE" else sha(ROOT / f"mutants/{impl}.patch"),
                             "expected_failing": ";".join(sorted(exp)), "observed_failing": ";".join(res["failed_ids"]),
                             "rc": res["rc"], "collected": res["collected"], "expected_collected": exp_count,
                             "non_assertion_failures": ";".join(res["non_assertion"]), "duration_s": res["duration_s"],
                             "verdict": verdict, "failed_nodes": ";".join(res["failed_nodes"]), "command": res["cmd"]})
                print(f"{impl:8} {suite:6} rc={res['rc']} collected={res['collected']} failed={';'.join(res['failed_ids']) or '-'} -> {verdict}")
    finally:
        shutil.rmtree(impls_dir, ignore_errors=True)
    with open(run_dir / "mutation_runs.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    (run_dir / "case_outputs.json").write_text(json.dumps(outputs, indent=1))
    env_info["utc_end"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    (run_dir / "environment.json").write_text(json.dumps(env_info, indent=1))
    print("run dir:", run_dir.relative_to(ROOT))


if __name__ == "__main__":
    main()
