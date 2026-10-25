
import json
import subprocess
import sys
from pathlib import Path

from financial_investigator import investigate_transactions
from scenario_registry import get_scenario

ROOT = Path(__file__).resolve().parent

WORKFLOWS = {
    "duplicate_transaction": {
        "script": "main.py",
        "report": "sandbox_verification_report.json",
        "patch": "proposed_patch.json",
    },
    "incorrect_refund": {
        "script": "refund_ai_repair.py",
        "report": "refund_verification_report.json",
        "patch": "refund_proposed_patch.json",
    },
    "monetary_precision": {
    "script": "precision_ai_repair.py",
    "report": "precision_verification_report.json",
    "patch": "precision_proposed_patch.json",
    },
}


def run_workflow(scenario_id):
    scenario = get_scenario(scenario_id)
    config = WORKFLOWS.get(scenario_id)

    if config is None:
        raise ValueError("Unsupported repair scenario.")

    financial = investigate_transactions(
        scenario["records"],
        calculator=scenario["calculator"],
    )

    report_path = ROOT / config["report"]
    patch_path = ROOT / config["patch"]

    report_path.unlink(missing_ok=True)
    patch_path.unlink(missing_ok=True)

    try:
        result = subprocess.run(
            [sys.executable, str(ROOT / config["script"])],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=600,
            check=False,
        )
        logs = result.stdout + "\n" + result.stderr

    except (OSError, subprocess.TimeoutExpired) as error:
        return {
            "scenario_id": scenario_id,
            "verified": False,
            "financial": financial,
            "verification": {},
            "patch": {},
            "logs": str(error),
        }

    
    try:
        verification = (
            json.loads(report_path.read_text(encoding="utf-8"))
            if report_path.exists()
            else {}
        )

        patch = (
            json.loads(patch_path.read_text(encoding="utf-8"))
            if patch_path.exists()
            else {}
        )

        if not isinstance(verification, dict):
            raise ValueError("Verification report must be a JSON object.")

        if not isinstance(patch, dict):
            raise ValueError("Patch report must be a JSON object.")

    except (OSError, ValueError) as error:
        return {
            "scenario_id": scenario_id,
            "verified": False,
            "financial": financial,
            "verification": {},
            "patch": {},
            "logs": logs + "\nReport error: " + str(error),
        }


    return {
        "scenario_id": scenario_id,
        "verified": (
            result.returncode == 0
            and verification.get("verdict") == "verified_fixed"
        ),
        "financial": financial,
        "verification": verification,
        "patch": patch,
        "logs": logs,
    }
if __name__ == "__main__":
    print("Available workflows:")
    for scenario_id in WORKFLOWS:
        scenario = get_scenario(scenario_id)
        print(scenario_id, "->", scenario["source_file"])
