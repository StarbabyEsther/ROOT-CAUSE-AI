
# ROOTCAUSE AI - REFUND PROCESSING SCENARIO

transactions = [
    {"id": "RF001", "type": "Payment", "amount": 150.00},
    {"id": "RF002", "type": "Refund", "amount": 50.00},
    {"id": "RF003", "type": "Payment", "amount": 100.00},
]


def calculate_total(transactions):
    total = 0

    for transaction in transactions:
        if transaction["type"] == "Payment":
            total += transaction["amount"]

        elif transaction["type"] == "Refund":
            # INTENTIONAL BUG: Refunds should be subtracted.
            total += transaction["amount"]

    return total


if __name__ == "__main__":
    print("Refund processor:", calculate_total(transactions))
