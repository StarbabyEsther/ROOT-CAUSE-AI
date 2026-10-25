
from transactions import transactions, calculate_total
from refund_processor import transactions as refund_transactions
from refund_processor import calculate_total as buggy_refund_total
from precision_processor import transactions as precision_transactions
from precision_processor import calculate_total as precision_calculator

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
    ,
"monetary_precision": {
    "records": precision_transactions,
    "calculator": precision_calculator,
    "source_file": "precision_processor.py"
    }
}



def get_scenario(scenario_id):
    if scenario_id not in SCENARIOS:
        raise ValueError("Unknown financial scenario")

    return SCENARIOS[scenario_id]
