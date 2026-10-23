
from transactions import transactions, calculate_total
from refund_processor import transactions as refund_transactions
from refund_processor import calculate_total as buggy_refund_total


SCENARIOS = {
    "duplicate_transaction": {
        "records": transactions,
        "calculator": calculate_total,
        "source_file": "transactions.py"
    },
    "incorrect_refund": {
        "records": refund_transactions,
        "calculator": buggy_refund_total,
        "source_file": "refund_processor.py"
    }
}


def get_scenario(scenario_id):
    if scenario_id not in SCENARIOS:
        raise ValueError("Unknown financial scenario")

    return SCENARIOS[scenario_id]
