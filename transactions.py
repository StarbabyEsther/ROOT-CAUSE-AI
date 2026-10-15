
# RootCause AI - Financial Transactions

transactions = [
    {
        "id": "TXN001",
        "type": "Payment",
        "amount": 150.00
    },
    {
        "id": "TXN002",
        "type": "Payment",
        "amount": 200.00
    },
    {
        "id": "TXN003",
        "type": "Refund",
        "amount": 50.00
    },
    {
        "id": "TXN004",
        "type": "Payment",
        "amount": 100.00
        },
    {
        "id": "TXN002",
        "type": "Payment",
        "amount": 200.00
}
]

# Function to calculate the net transaction amount
def calculate_total(transactions):
    total = 0

    for transaction in transactions:
        if transaction["type"] == "Payment":
            total = total + transaction["amount"]

        elif transaction["type"] == "Refund":
            total = total - transaction["amount"]

    return total


# Call the function

if __name__ == "__main__":
    result = calculate_total(transactions)
    print("Net transaction amount: $", result)







