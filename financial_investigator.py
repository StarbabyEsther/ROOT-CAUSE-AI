
# ROOTCAUSE AI - Financial Investigation Engine
# Detects financial discrepancies and identifies affected transactions.

import json
from decimal import Decimal
from collections import Counter
from transactions import transactions, calculate_total


def investigate_transactions(records):
    """
    Independently investigate transaction processing results.
    """

    # STEP 1: Identify repeated transaction IDs
    ids = [transaction["id"] for transaction in records]
    counts = Counter(ids)

    duplicate_ids = [
        txn_id for txn_id, count in counts.items()
        if count > 1
    ]

    # STEP 2: Obtain the application's calculated total
    actual_total = Decimal(str(calculate_total(records)))

    # STEP 3: Independently calculate expected financial results
    expected_total = Decimal("0.00")
    seen_ids = set()
    affected_transactions = []

    for transaction in records:
        txn_id = transaction["id"]
        amount = Decimal(str(transaction["amount"]))

        if txn_id in seen_ids:
            affected_transactions.append(txn_id)
            continue

        seen_ids.add(txn_id)

        if transaction["type"] == "Payment":
            expected_total += amount

        elif transaction["type"] == "Refund":
            expected_total -= amount

    # STEP 4: Calculate the financial discrepancy
    discrepancy = actual_total - expected_total

    # STEP 5: Create structured investigation evidence
    report = {
        "issue_detected": discrepancy != 0,
        "issue_type": "Possible duplicate processing"
                      if duplicate_ids else "Unknown discrepancy",
        "duplicate_ids": duplicate_ids,
        "affected_transactions": affected_transactions,
        "actual_total": str(actual_total),
        "expected_total": str(expected_total),
        "discrepancy": str(discrepancy)
    }

    return report


if __name__ == "__main__":
    report = investigate_transactions(transactions)

    print("\nROOTCAUSE AI - FINANCIAL INVESTIGATION")
    print("=" * 45)

    for key, value in report.items():
        print(f"{key}: {value}")
    with open("financial_report.json", "w", encoding="utf-8") as file:
        json.dump(report, file, indent=4)

    print("\nFinancial investigation report saved!")