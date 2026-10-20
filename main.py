from repair_verifier import verify_repair
from nemotron_client import investigate_bug

import json

from financial_investigator import investigate_transactions
from transactions import transactions

print("=" * 45)
print("ROOTCAUSE AI - FINANCIAL DEBUGGING AGENT")
print("=" * 45)

print("Starting RootCause AI...")


# Step 1: Investigate financial transactions
print("\nInvestigating financial transactions...")

report = investigate_transactions(transactions)

print("Issue detected:", report["issue_detected"])
print("Issue type:", report["issue_type"])
print("Expected total: $", report["expected_total"])
print("Actual total: $", report["actual_total"])
print("Discrepancy: $", report["discrepancy"])


# Save the investigation report for Nemotron
with open("financial_report.json", "w", encoding="utf-8") as file:
    json.dump(report, file, indent=4)

print("Financial investigation report saved successfully!")


# Step 2: Ask NVIDIA Nemotron to investigate the bug
print("\nStarting NVIDIA Nemotron investigation...")

ai_result = investigate_bug()

print("\nAI INVESTIGATION RESULTS:")
print(ai_result)


# Convert Nemotron's JSON response into a Python dictionary
ai_report = json.loads(ai_result)

print("\nSTRUCTURED AI RESULTS:")
print("Issue type:", ai_report["issue_type"])
print("Affected function:", ai_report["affected_function"])
print("Root cause:", ai_report["root_cause"])
print("Suggested fix:", ai_report["suggested_fix"])


# Check that Nemotron provided all required information
required_fields = [
    "issue_type",
    "affected_function",
    "root_cause",
    "suggested_fix"
]

if all(field in ai_report for field in required_fields):
    print("AI repair proposal validated successfully!")
else:
    print("AI repair proposal is missing information!")



# Step 3: Verify the controlled repair
print("\nStarting repair verification...")

verify_repair()

print("\nRootCause AI workflow completed!")