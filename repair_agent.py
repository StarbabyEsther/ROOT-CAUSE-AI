
from pathlib import Path
import json

from patch_generator import generate_patch
from patch_validator import validate_patch


MAX_ATTEMPTS = 2


def run_repair_agent():
    feedback = None
    print("ROOTCAUSE AI - AUTONOMOUS REPAIR AGENT")
    print("=" * 45)

    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f"\nAttempt {attempt}/{MAX_ATTEMPTS}")

        try:
            patch = generate_patch(feedback=feedback)
            valid, reason = validate_patch()

            if valid:
                print("Structural validation: PASSED")
                print("Patch is ready for isolated verification.")
                print("Status: NOT VERIFIED")
                return

            print("Structural validation: FAILED")
            print("Reason:", reason)

            feedback = (
                f"The previous patch was rejected because: {reason}. "
                "Generate a corrected patch that addresses this problem. "
                "Preserve all original transaction records exactly. "
                "Only modify the logic inside calculate_total(). "
                "Make sure payments are added and refunds are subtracted. "
                "Return exactly one valid JSON object."
            )

            if attempt < MAX_ATTEMPTS:
                print("Requesting another patch from Nemotron...")

        except Exception as error:
            print("Repair attempt failed:", error)
            
            feedback = (
                f"The previous attempt failed because: {error}. "
                "Return exactly one valid JSON object. "
                "Do not include Markdown formatting or extra text."
            )

    print("\nMaximum repair attempts reached.")
    print("Status: NO VERIFIED REPAIR")


if __name__ == "__main__":
    run_repair_agent()
