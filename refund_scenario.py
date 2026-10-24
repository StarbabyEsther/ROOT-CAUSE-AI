
from financial_investigator import investigate_transactions


# Synthetic transactions for the refund scenario.
refund_transactions = [
    {
        "id": "RF001",
        "type": "Payment",
        "amount": 150.00
    },
    {
        "id": "RF002",
        "type": "Refund",
        "amount": 50.00
    },
    {
        "id": "RF003",
        "type": "Payment",
        "amount": 100.00
    }
]


# Intentionally buggy software for testing.
def buggy_refund_total(records):
    total = 0

    for transaction in records:
        if transaction["type"] == "Payment":
            total += transaction["amount"]

        elif transaction["type"] == "Refund":
            # BUG: Refunds should be SUBTRACTED.
            total += transaction["amount"]

    return total


if __name__ == "__main__":
    report = investigate_transactions(
        refund_transactions,
        calculator=buggy_refund_total
    )

    print("ROOTCAUSE AI - REFUND ERROR SCENARIO")
    print("=" * 45)

    for key, value in report.items():
        print(f"{key}: {value}")
