"""Simulated investigation child used by the M1 tests.

Speaks the launcher's `RCAI_` marker protocol and writes the same artifacts, but
never touches the network, the model or a sandbox. Behaviour is controlled by
environment variables so a test can simulate success, mismatch and failure:

    FAKE_MODE            ok | mismatch | crash | hang | partial
    FAKE_CANDIDATE       "1" to write a bundle candidate file
    FAKE_ECHO_SECRET     a string to echo (proves the scrubber is wired)
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

MARKER = "RCAI_"

FINANCIAL = {
    "duplicate_transaction": {
        "issue_detected": True,
        "issue_type": "Possible duplicate processing",
        "duplicate_ids": ["TXN002"],
        "affected_transactions": ["TXN002"],
        "actual_total": "600.0",
        "expected_total": "400.00",
        "discrepancy": "200.00",
    },
    "incorrect_refund": {
        "issue_detected": True,
        "issue_type": "Possible refund sign error",
        "duplicate_ids": [],
        "affected_transactions": ["RF002"],
        "actual_total": "300.0",
        "expected_total": "200.00",
        "discrepancy": "100.00",
    },
    "monetary_precision": {
        "issue_detected": True,
        "issue_type": "Unclassified financial discrepancy",
        "duplicate_ids": [],
        "affected_transactions": [],
        "actual_total": "0.20000000000000004",
        "expected_total": "0.20",
        "discrepancy": "4E-17",
    },
}

CANDIDATES = {
    "duplicate_transaction": "verification_bundle/transactions.py",
    "incorrect_refund": "refund_verification_bundle/refund_processor.py",
    "monetary_precision": "precision_verification_bundle/precision_processor.py",
}

TEST_NAMES = {
    "duplicate_transaction": 6,
    "incorrect_refund": 7,
    "monetary_precision": 5,
}


def emit(kind: str, payload: object) -> None:
    sys.stdout.write(f"{MARKER}{kind} {json.dumps(payload)}\n")
    sys.stdout.flush()


def candidate_logs(count: int) -> str:
    lines = ["test_empty_transactions (suite.Tests.test_empty_transactions) ... ok"]
    for index in range(1, count):
        lines.append(f"test_case_{index} (suite.Tests.test_case_{index}) ... ok")
    lines.append("")
    lines.append("----------------------------------------------------------------------")
    lines.append(f"Ran {count} tests in 0.002s")
    lines.append("")
    lines.append("OK")
    return "\n".join(lines)


def main() -> int:
    scenario = sys.argv[1] if len(sys.argv) > 1 else "duplicate_transaction"
    mode = os.getenv("FAKE_MODE", "ok")
    job_dir = Path.cwd()

    echo = os.getenv("FAKE_ECHO_SECRET", "")
    if echo:
        print(f"debug: connecting with api_key={echo}")
        sys.stdout.flush()

    emit("EVENT", {"stage": "investigate", "status": "running"})
    emit("FINANCIAL", FINANCIAL[scenario])
    emit("EVENT", {"stage": "investigate", "status": "done"})
    emit("EVENT", {"stage": "diagnose", "status": "running"})

    if mode == "hang":
        time.sleep(600)
        return 0

    if mode == "crash":
        emit("ERROR", {"message": "Simulated backend failure: connection refused"})
        return 1

    emit("EVENT", {"stage": "diagnose", "status": "done"})
    emit("EVENT", {"stage": "repair", "status": "done"})
    emit("EVENT", {"stage": "verify", "status": "running"})

    expected = TEST_NAMES[scenario]
    logs = candidate_logs(expected)

    patch = {
        "root_cause": "calculate_total() re-processes transactions that share an id.",
        "explanation": "A duplicate transaction id is accumulated twice.",
        "target_file": {
            "duplicate_transaction": "transactions.py",
            "incorrect_refund": "refund_processor.py",
            "monetary_precision": "precision_processor.py",
        }[scenario],
        "proposed_code": "def calculate_total(transactions):\n    return 42\n",
    }

    if mode != "partial":
        (job_dir / "proposed_patch.json").write_text(json.dumps(patch), encoding="utf-8")

        candidate_path = job_dir / CANDIDATES[scenario]
        candidate_path.parent.mkdir(parents=True, exist_ok=True)
        candidate_path.write_text("# candidate repair\n" + patch["proposed_code"], encoding="utf-8")

    passed = expected
    if mode == "mismatch":
        # Claim success while the suite does not add up.
        passed = expected - 1

    emit("EVENT", {"stage": "verify", "status": "done"})
    emit(
        "RESULT",
        {
            "scenario_id": scenario,
            "verified": mode not in {"mismatch", "partial"},
            "financial": FINANCIAL[scenario],
            "verification": {
                "scenario_id": "refund_sign_error" if scenario == "incorrect_refund" else scenario,
                "verdict": "verified_fixed" if mode != "partial" else "not_fixed",
                "attempts": 1,
                "final_passed": passed,
                "final_failed": expected - passed,
                "logs": logs,
            },
            "patch": patch,
            "logs": "[1/4] FINANCIAL INVESTIGATION\n[2/4] NVIDIA NEMOTRON INVESTIGATION\n"
            "[3/4] AUTONOMOUS AI REPAIR\n[4/4] FINAL VERIFICATION RESULTS",
        },
    )
    emit(
        "AST",
        {
            "passed": True,
            "reason": "Structural validation passed; NOT VERIFIED.",
            "negativeControl": {"passed": False, "reason": "Patch must contain only calculate_total()."},
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
