
import json
import re
import subprocess
import time
from pathlib import Path

from prepare_sandbox_tests import prepare_sandbox_tests

ROOT = Path(__file__).resolve().parent
EXPECTED_TESTS = 6


def run_sandbox_tests(source_file):
    command = [
        "contree", "run",
        "--use", "tag:python:3.12-slim",
        "--file", f"./{source_file}:/app/transactions.py",
        "--file",
        "./verification_bundle/test_financial_regression.py:"
        "/app/test_financial_regression.py",
        "--disposable",
        "--",
        "python", "-m", "unittest",
        "discover",
        "-s", "/app",
        "-p", "test_financial_regression.py",
        "-v",
    ]

    result = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=240,
        check=False,
    )

    output = result.stdout + "\n" + result.stderr

    count = re.search(r"Ran (\d+) tests?", output)
    ran = int(count.group(1)) if count else 0

    failed = re.search(r"failures=(\d+)", output)
    errors = re.search(r"errors=(\d+)", output)

    failure_count = int(failed.group(1)) if failed else 0
    error_count = int(errors.group(1)) if errors else 0

    if (
        re.search(r"(?m)^OK\s*$", output)
        and result.returncode == 0
    ):
        status = "PASSED"
    elif re.search(r"(?m)^FAILED\b", output):
        status = "FAILED"
    else:
        status = "ERROR"

    return {
        "status": status,
        "ran": ran,
        "passed": max(0, ran - failure_count - error_count)
        if status != "ERROR" else 0,
        "failed": failure_count + error_count,
        "return_code": result.returncode,
        "logs": output,
    }


def verify_ai_repair():
    started = time.monotonic()

    print("ROOTCAUSE AI - AUTOMATED SANDBOX VERIFICATION")
    print("=" * 50)

    # Builds the repaired copy and test files.
    # Does not execute AI-generated code locally.
    prepare_sandbox_tests()

    print("\nTesting ORIGINAL code in Nebius Sandbox...")
    baseline = run_sandbox_tests("transactions.py")
    print("\nORIGINAL SANDBOX ERROR DETAILS:")
    print(baseline["logs"])

    print("Baseline:", baseline["status"])
    print("Failures:", baseline["failed"])

    print("\nTesting NEMOTRON REPAIR in Nebius Sandbox...")
    repaired = run_sandbox_tests(
        "verification_bundle/transactions.py"
    )
    print("\nREPAIRED SANDBOX ERROR DETAILS:")
    print(repaired["logs"])

    print("Repair:", repaired["status"])
    print("Tests passed:", repaired["passed"])

    valid_comparison = (
        baseline["ran"] == EXPECTED_TESTS
        and repaired["ran"] == EXPECTED_TESTS
        and baseline["status"] == "FAILED"
        and baseline["failed"] > 0
    )

    if not valid_comparison:
        verdict = "error"
    elif repaired["status"] == "PASSED":
        verdict = "verified_fixed"
    elif repaired["status"] == "FAILED":
        verdict = "not_fixed"
    else:
        verdict = "error"

    report = {
        "scenario_id": "duplicate_transaction",
        "baseline_passed": baseline["passed"],
        "baseline_failed": baseline["failed"],
        "final_passed": repaired["passed"],
        "final_failed": repaired["failed"],
        "verdict": verdict,
        "elapsed_seconds": round(
            time.monotonic() - started, 2
        ),
        "baseline_logs": baseline["logs"],
        "repair_logs": repaired["logs"],
    }

    Path("sandbox_verification_report.json").write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    print("\nFINAL VERDICT:", verdict)
    print("Report saved: sandbox_verification_report.json")

    if verdict != "verified_fixed":
        print("Check the report for test failures or errors.")

    return report

if __name__ == "__main__":
    verify_ai_repair()
