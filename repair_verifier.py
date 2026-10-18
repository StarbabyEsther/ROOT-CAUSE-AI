import json
import inspect
import subprocess
import sys
# shutil is for copying files
import shutil
import tempfile
from pathlib import Path
from unittest import result

def corrected_total(transactions):
    total = 0
    seen_ids = set()

    for transaction in transactions:
        if transaction["id"] in seen_ids:
            continue

        seen_ids.add(transaction["id"])

        if transaction["type"] == "Payment":
            total += transaction["amount"]

        elif transaction["type"] == "Refund":
            total -= transaction["amount"]

    return total


# Test our corrected function using the original transactions
from transactions import transactions

def verify_repair():
    # Create a temporary folder for testing repairs
    with tempfile.TemporaryDirectory() as folder:
        print("Temporary testing folder:", folder)

        # Create a file path inside that folder
        test_file = Path(folder) / "transactions.py"

        print("Test file location:", test_file)

            
            # Copy the original transaction processor
        shutil.copy("transactions.py", test_file)
            
            # Get the code from our corrected function
        corrected_code = inspect.getsource(corrected_total)

            # Rename it to match the function our test expects
        corrected_code = corrected_code.replace(
                "def corrected_total(",
                "def calculate_total("
            )

            # Write the corrected function into the temporary copy
        test_file.write_text(corrected_code, encoding="utf-8")

        print("Correction applied to temporary copy!")


        print("Transaction processor copied successfully!")
        print("Copy exists:", test_file.exists())
            
            # Create a path for our test file
        test_copy = Path(folder) / "test_transactions.py"

        # Copy our automated test into the temporary folder
        shutil.copy("test_transactions.py", test_copy)

        print("Test copied successfully!")
        print("Test copy exists:", test_copy.exists())

        
        # Run pytest using our temporary copies
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-v"],
            cwd=folder,
            # current working directory
            capture_output=True,
            text=True,
            # Make the results readable
            timeout=30
        )

        print("TEMPORARY TEST RESULTS:")
        print(result.stdout)
        print(result.stderr)
    
    # Check whether the repair passed all tests
        if result.returncode == 0:
            print("REPAIR VERIFIED SUCCESSFULLY!")
        else:
            print("REPAIR FAILED VERIFICATION!")
        
    # Create a verification report
        verification_report = {
        "repair_verified": result.returncode == 0,
        "test_status": "PASSED" if result.returncode == 0 else "FAILED",
        "return_code": result.returncode
    }

    # Save the report as a JSON file
        with open("verification_report.json", "w", encoding="utf-8") as file:
            json.dump(verification_report, file, indent=4)

        print("Verification report saved successfully!")
    
if __name__ == "__main__":
    verify_repair()
    print("Repair verification process completed!")


