
# ROOTCAUSE AI - Financial Investigation Engine

import json
from decimal import Decimal
from collections import Counter
from transactions import transactions, calculate_total


def investigate_transactions(records, calculator=None):
    """
    Independently examine a financial calculation.
    An optional calculator allows different bug scenarios.
    """

    if calculator is None:
        calculator = calculate_total

    # Identify duplicate transaction IDs.
    ids = [transaction["id"] for transaction in records]
    counts = Counter(ids)

    duplicate_ids = [
        txn_id for txn_id, count in counts.items()
        if count > 1
    ]

    # Obtain the application's actual result.
    actual_total = Decimal(str(calculator(records)))

    # Calculate expected results independently.
    expected_total = Decimal("0.00")
    duplicate_impact = Decimal("0.00")
    refund_total = Decimal("0.00")

    seen_ids = set()
    refund_ids = []
    affected_transactions = []

    for transaction in records:
        txn_id = transaction["id"]
        txn_type = transaction["type"]
        amount = Decimal(str(transaction["amount"]))

        if txn_type == "Payment":
            signed_amount = amount
        elif txn_type == "Refund":
            signed_amount = -amount
        else:
            raise ValueError(
                f"Unknown transaction type: {txn_type}"
            )

        if txn_id in seen_ids:
            duplicate_impact += signed_amount
            affected_transactions.append(txn_id)
            continue

        seen_ids.add(txn_id)
        expected_total += signed_amount

        if txn_type == "Refund":
            refund_total += amount
            refund_ids.append(txn_id)

    discrepancy = actual_total - expected_total

    # Classify the likely cause using financial evidence.
    if discrepancy == 0:
        issue_type = "No discrepancy"

    elif (
        duplicate_ids
        and discrepancy == duplicate_impact
    ):
        issue_type = "Possible duplicate processing"

    elif (
        not duplicate_ids
        and refund_total != 0
        and discrepancy == 2 * refund_total
    ):
        issue_type = "Possible refund sign error"
        affected_transactions = refund_ids

    else:
        issue_type = "Unclassified financial discrepancy"

    report = {
        "issue_detected": discrepancy != 0,
        "issue_type": issue_type,
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

    with open(
        "financial_report.json", "w", encoding="utf-8"
    ) as file:
        json.dump(report, file, indent=4)

    print("\nFinancial investigation report saved!")
