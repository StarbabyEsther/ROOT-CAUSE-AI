
import copy
import unittest

from refund_processor import calculate_total, transactions


class RefundRegressionTests(unittest.TestCase):

    def test_original_total(self):
        self.assertEqual(calculate_total(transactions), 200)

    def test_refund_only(self):
        data = [
            {"id": "A", "type": "Refund", "amount": 25}
        ]
        self.assertEqual(calculate_total(data), -25)

    def test_multiple_refunds(self):
        data = [
            {"id": "A", "type": "Payment", "amount": 100},
            {"id": "B", "type": "Refund", "amount": 20},
            {"id": "C", "type": "Refund", "amount": 10},
        ]
        self.assertEqual(calculate_total(data), 70)

    def test_payments_only(self):
        data = [
            {"id": "A", "type": "Payment", "amount": 40},
            {"id": "B", "type": "Payment", "amount": 60},
        ]
        self.assertEqual(calculate_total(data), 100)

    def test_empty_transactions(self):
        self.assertEqual(calculate_total([]), 0)

    def test_input_not_modified(self):
        original = copy.deepcopy(transactions)
        calculate_total(transactions)
        self.assertEqual(transactions, original)

    def test_original_records_preserved(self):
        self.assertEqual(
            transactions,
            [
                {"id": "RF001", "type": "Payment", "amount": 150.00},
                {"id": "RF002", "type": "Refund", "amount": 50.00},
                {"id": "RF003", "type": "Payment", "amount": 100.00},
            ]
        )


if __name__ == "__main__":
    unittest.main()
