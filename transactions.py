
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
    }
]


for transaction in transactions:
    print("Transaction ID:", transaction["id"])
    print("Type:", transaction["type"])
    print("Amount: $", transaction["amount"])
    print("--------------------")


