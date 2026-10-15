# use the calculate_total() function i  created in transactions.py
from transactions import calculate_total

# defining a test function
def test_duplicate_transaction():
    transactions = [
        {"id": "TXN001", "type": "Payment", "amount": 150.00},
        {"id": "TXN002", "type": "Payment", "amount": 200.00},
        {"id": "TXN003", "type": "Refund", "amount": 50.00},
        {"id": "TXN004", "type": "Payment", "amount": 100.00},
        {"id": "TXN002", "type": "Payment", "amount": 200.00}
    ]

    result = calculate_total(transactions)

#I expect the result to equal 400. If it doesn't, this test should fail.
    assert result == 400.00
