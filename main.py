
import json
from pathlib import Path

from financial_investigator import investigate_transactions
from nemotron_client import investigate_bug
from repair_agent import run_repair_agent
from transactions import transactions


REQUIRED_AI_FIELDS = [
    "issue_type",
    "affected_function",
    "root_cause",
    "suggested_fix",
]


def validate_ai_response(response):
    """Validate Nemotron's structured diagnosis."""

    if isinstance(response, str):
        try:
            data = json.loads(response)
        except json.JSONDecodeError as error:
            raise ValueError(
                "Nemotron returned invalid JSON."
            ) from error

    elif isinstance(response, dict):
        data = response

    else:
        raise ValueError(
            "Nemotron response must be a JSON object."
        )

    if not isinstance(data, dict):
        raise ValueError(
            "Nemotron response must contain a JSON object."
        )

    invalid_fields = [
        field
        for field in REQUIRED_AI_FIELDS
        if not isinstance(data.get(field), str)
        or not data[field].strip()
    ]

    if invalid_fields:
        raise ValueError(
            "Missing, empty, or invalid AI fields: "
            + ", ".join(invalid_fields)
        )

    return data


def main():
    print("=" * 50)
    print("ROOTCAUSE AI - AUTONOMOUS FINANCIAL DEBUGGING")
    print("=" * 50)

    # STEP 1: Investigate financial transactions
    print("\n[1/4] FINANCIAL INVESTIGATION")

    report = investigate_transactions(transactions)

    print("Issue detected:", report["issue_detected"])
    print("Issue type:", report["issue_type"])
    print("Actual total: $", report["actual_total"])
    print("Expected total: $", report["expected_total"])
    print("Discrepancy: $", report["discrepancy"])

    Path("financial_report.json").write_text(
        json.dumps(report, indent=4),
        encoding="utf-8"
    )

    if not report["issue_detected"]:
        print("\nNo discrepancy detected.")
        print("No repair requested.")
        return 0

    # STEP 2: NVIDIA Nemotron diagnosis
    print("\n[2/4] NVIDIA NEMOTRON INVESTIGATION")

    try:
        ai_result = investigate_bug()
        ai_report = validate_ai_response(ai_result)

    except Exception as error:
        print("AI investigation failed:", error)
        print("Repair workflow stopped.")
        return 1

    print("Structured AI response validated!")

    print("Issue type:", ai_report["issue_type"])
    print("Affected function:", ai_report["affected_function"])
    print("Root cause:", ai_report["root_cause"])
    print("Suggested fix:", ai_report["suggested_fix"])

    # STEP 3: Generate and validate the AI repair
    print("\n[3/4] AUTONOMOUS AI REPAIR")

    print("Starting Nemotron patch generation...")
    print("Maximum attempts: 2")

    try:
        verification = run_repair_agent()
    except Exception as error:
        print("Repair workflow failed:", error)
        return 1

    # STEP 4: Display independent verification
    print("\n[4/4] FINAL VERIFICATION RESULTS")

    if (
        isinstance(verification, dict)
        and verification.get("verdict") == "verified_fixed"
    ):
        print("Status: VERIFIED AGAINST FINANCIAL TESTS")
        print(
            "Baseline failed:",
            verification["baseline_failed"]
        )
        print(
            "Final tests passed:",
            verification["final_passed"]
        )
        print(
            "Final tests failed:",
            verification["final_failed"]
        )
        print(
            "Verification time:",
            verification["elapsed_seconds"],
            "seconds"
        )

        print("\nROOTCAUSE AI WORKFLOW COMPLETED!")
        print("Report: sandbox_verification_report.json")
        return 0

    print("Status: NO VERIFIED REPAIR")
    print("Review the repair and sandbox logs.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
