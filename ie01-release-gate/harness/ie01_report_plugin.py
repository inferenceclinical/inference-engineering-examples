"""pytest plugin (-p ie01_report_plugin): writes per-test outcome and exception class to $IE01_REPORT as JSON."""
import json
import os

import pytest

_results = []


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item, call):
    report = yield
    if report.when == "call" or report.outcome != "passed":
        exc = call.excinfo.typename if (call.excinfo is not None and report.outcome == "failed") else None
        _results.append({"nodeid": report.nodeid, "when": report.when, "outcome": report.outcome, "exception": exc})
    return report


def pytest_sessionfinish(session, exitstatus):
    path = os.environ.get("IE01_REPORT")
    if path:
        with open(path, "w") as fh:
            json.dump({"exitstatus": int(exitstatus), "collected": session.testscollected, "results": _results}, fh, indent=1)
