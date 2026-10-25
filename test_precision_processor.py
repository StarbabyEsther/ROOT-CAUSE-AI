
import unittest
from decimal import Decimal

from precision_processor import calculate_total, transactions


class PrecisionRegressionTests(unittest.TestCase):

    def test_original_total(self):
        result = Decimal(str(calculate_total(transactions)))
        self.assertEqual(result, Decimal("0.20"))

    def test_decimal_accuracy(self):
        data = [
            {"id": "A", "type": "Payment", "amount": 0.10},
            {"id": "B", "type": "Payment", "amount": 0.20},
        ]

        result = Decimal(str(calculate_total(data)))

        self.assertEqual(result, Decimal("0.30"))

    def test_multiple_payments(self):
        data = [
            {"id": "A", "type": "Payment", "amount": 0.10},
            {"id": "B", "type": "Payment", "amount": 0.20},
            {"id": "C", "type": "Payment", "amount": 0.30},
        ]

        result = Decimal(str(calculate_total(data)))

        self.assertEqual(result, Decimal("0.60"))

    def test_refund_precision(self):
        data = [
            {"id": "A", "type": "Payment", "amount": 0.30},
            {"id": "B", "type": "Refund", "amount": 0.10},
        ]

        result = Decimal(str(calculate_total(data)))

        self.assertEqual(result, Decimal("0.20"))

    def test_empty_transactions(self):
        self.assertEqual(calculate_total([]), 0)


if __name__ == "__main__":
    unittest.main()
