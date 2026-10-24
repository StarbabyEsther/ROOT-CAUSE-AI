
from scenario_registry import get_scenario
from financial_investigator import investigate_transactions


def test_duplicate_transaction_scenario():
    scenario = get_scenario("duplicate_transaction")

    report = investigate_transactions(
        scenario["records"],
        calculator=scenario["calculator"]
    )

    assert report["issue_detected"] is True
    assert report["issue_type"] == "Possible duplicate processing"
    assert report["discrepancy"] == "200.00"


def test_incorrect_refund_scenario():
    scenario = get_scenario("incorrect_refund")

    report = investigate_transactions(
        scenario["records"],
        calculator=scenario["calculator"]
    )

    assert report["issue_detected"] is True
    assert report["issue_type"] == "Possible refund sign error"
    assert report["discrepancy"] == "100.00"
