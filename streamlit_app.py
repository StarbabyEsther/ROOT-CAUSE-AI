
import difflib
import json
import subprocess
import sys
from pathlib import Path

import streamlit as st

from financial_investigator import investigate_transactions
from transactions import (
    transactions as duplicate_records,
    calculate_total as duplicate_calculator,
)
from refund_processor import (
    transactions as refund_records,
    calculate_total as refund_calculator,
)


ROOT = Path(__file__).resolve().parent

SCENARIOS = {
    "Duplicate transaction processing": {
        "script": "main.py",
        "report": "sandbox_verification_report.json",
        "patch": "proposed_patch.json",
        "original": "transactions.py",
        "repaired": "verification_bundle/transactions.py",
        "records": duplicate_records,
        "calculator": duplicate_calculator,
        "total_tests": 6,
    },
    "Incorrect refund calculation": {
        "script": "refund_ai_repair.py",
        "report": "refund_verification_report.json",
        "patch": "refund_proposed_patch.json",
        "original": "refund_processor.py",
        "repaired": "refund_verification_bundle/refund_processor.py",
        "records": refund_records,
        "calculator": refund_calculator,
        "total_tests": 7,
    },
}


st.set_page_config(
    page_title="RootCause AI",
    page_icon="🔍",
    layout="wide",
)

st.title("🔍 RootCause AI")
st.caption(
    "Autonomous Financial Software Debugging | "
    "NVIDIA Nemotron + Nebius Sandboxes"
)

st.write(
    "RootCause AI detects financial software errors, "
    "investigates root causes, generates proposed repairs, "
    "and independently verifies them in isolated sandboxes."
)

st.divider()

st.subheader("Select a Financial Investigation")

scenario_name = st.selectbox(
    "Choose a financial software bug",
    list(SCENARIOS.keys()),
)

scenario = SCENARIOS[scenario_name]

st.info(
    "This demonstration uses synthetic financial data. "
    "Original source code is preserved."
)
st.write(
    f"**Verification suite:** "
    f"{scenario['total_tests']} financial regression tests"
)


if st.button("🚀 Analyze & Repair", type="primary"):

    report_path = ROOT / scenario["report"]
    patch_path = ROOT / scenario["patch"]

    # Avoid displaying reports from an earlier run.
    report_path.unlink(missing_ok=True)
    patch_path.unlink(missing_ok=True)

    try:
        with st.spinner(
            "Nemotron is investigating and Nebius is "
            "verifying the proposed repair..."
        ):

            result = subprocess.run(
                [sys.executable, str(ROOT / scenario["script"])],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=600,
                check=False,
            )

        logs = result.stdout + "\n" + result.stderr

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

        financial = investigate_transactions(
            scenario["records"],
            calculator=scenario["calculator"],
        )

        verified = (
            result.returncode == 0
            and verification.get("verdict") == "verified_fixed"
        )

        st.session_state["rc_result"] = {
            "scenario": scenario_name,
            "verified": verified,
            "financial": financial,
            "verification": verification,
            "patch": patch,
            "logs": logs,
        }

    except Exception as error:
        st.session_state["rc_result"] = {
            "scenario": scenario_name,
            "verified": False,
            "financial": {},
            "verification": {},
            "patch": {},
            "logs": str(error),
        }


results = st.session_state.get("rc_result")

if results and results["scenario"] == scenario_name:

    financial = results["financial"]
    verification = results["verification"]
    patch = results["patch"]

    st.divider()

    st.header("Investigation Results")

    if results["verified"]:
        st.success(
            "AI-generated repair VERIFIED against "
            "the selected financial regression tests."
        )
    else:
        st.error(
            "No verified repair was obtained for this run. "
            "Review the execution logs."
        )

    if financial:

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Financial Discrepancy",
            f"${float(financial['discrepancy']):,.2f}",
        )

        col2.metric(
            "Actual Total",
            f"${float(financial['actual_total']):,.2f}",
        )

        col3.metric(
            "Expected Total",
            f"${float(financial['expected_total']):,.2f}",
        )

        st.write(
            "**Issue Detected:**",
            financial["issue_type"],
        )

        st.write("**Affected Transactions:**")

        st.code(
            json.dumps(
                financial.get("affected_transactions", []),
                indent=2
            ),
            language="json"
        )

    st.divider()

    st.header("🧠 NVIDIA Nemotron Investigation")

    if patch:
        st.write(
            "**Root Cause:**",
            patch.get("root_cause", "Not available"),
        )

        st.write(
            "**Explanation:**",
            patch.get("explanation", "Not available"),
        )

        st.subheader("AI-Generated Code Repair")

        st.code(
            patch.get("proposed_code", ""),
            language="python",
        )

    else:
        st.warning("No valid AI repair proposal was saved.")

    st.divider()

    st.header("🛡️ Nebius Sandbox Verification")

    if verification:

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Original Tests Failed",
            verification.get("baseline_failed", "N/A"),
        )

        col2.metric(
            "Repaired Tests Passed",
            verification.get("final_passed", "N/A"),
        )

        col3.metric(
            "Repaired Tests Failed",
            verification.get("final_failed", "N/A"),
        )

        st.write(
            "**Verdict:**",
            verification.get("verdict", "Unknown"),
        )

        if "elapsed_seconds" in verification:
            st.write(
                "**Verification Time:**",
                verification["elapsed_seconds"],
                "seconds",
            )

        if "attempts" in verification:
            st.write(
                "**Repair Attempts:**",
                verification["attempts"],
            )

    if results["verified"]:

        original_file = ROOT / scenario["original"]
        repaired_file = ROOT / scenario["repaired"]

        if original_file.exists() and repaired_file.exists():

            original_code = original_file.read_text(
                encoding="utf-8"
            )

            repaired_code = repaired_file.read_text(
                encoding="utf-8"
            )

            diff = "".join(
                difflib.unified_diff(
                    original_code.splitlines(keepends=True),
                    repaired_code.splitlines(keepends=True),
                    fromfile="Original",
                    tofile="AI Repaired",
                )
            )

            st.subheader("Code Changes: Before vs. After")
            st.code(diff or "No code differences found.", language="diff")

    with st.expander("View Complete Execution Logs"):
        st.text_area(
            "Execution evidence",
            results["logs"],
            height=300,
        )

st.divider()

st.caption(
    "RootCause AI verifies candidate repairs against "
    "specific protected tests. Verification does not "
    "guarantee correctness for every possible scenario."
)
