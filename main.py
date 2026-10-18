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


