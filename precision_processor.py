
# ROOTCAUSE AI - MONETARY PRECISION SCENARIO
# Intentionally faulty financial calculation.

transactions = [
    {"id": "PR001", "type": "Payment", "amount": 0.10},
    {"id": "PR002", "type": "Payment", "amount": 0.20},
    {"id": "PR003", "type": "Refund", "amount": 0.10},
]


def calculate_total(transactions):
    total = 0.0

    for transaction in transactions:
        if transaction["type"] == "Payment":
            total += transaction["amount"]

        elif transaction["type"] == "Refund":
            total -= transaction["amount"]

    return total


if __name__ == "__main__":
    print("Calculated total:", calculate_total(transactions))
