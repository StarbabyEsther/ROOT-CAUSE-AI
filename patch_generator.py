
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

API_KEY = os.getenv("NEBIUS_API_KEY")
MODEL_ID = os.getenv("NEBIUS_MODEL")

if not API_KEY or not MODEL_ID:
    raise RuntimeError("Missing Nebius configuration in .env")

client = OpenAI(
    base_url="https://api.tokenfactory.nebius.com/v1/",
    api_key=API_KEY,
    timeout=60.0
)


def generate_patch():
    report = json.loads(
        Path("financial_report.json").read_text(encoding="utf-8")
    )

    source_code = Path("transactions.py").read_text(
        encoding="utf-8"
    )

    response = client.chat.completions.create(
        model=MODEL_ID,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert Python code repair agent. "
                    "Return only a valid JSON object with these keys: "
                    "root_cause, explanation, target_file, "
                    "proposed_code. "
                    "target_file must be transactions.py. "
                    "proposed_code must contain the full corrected "
                    "Python source code. "
                    "Preserve public function names and signatures. "
                    "Do not modify tests, fixtures, or expected values. "
                    "Do not include Markdown formatting. "
                    "Never claim the patch is verified."
                )
            },
            {
                "role": "user",
                "content": (
                    "You are RootCause AI, an autonomous Python software "
                    "repair engineer specializing in financial applications. "

                    "Your goal is to repair the underlying SOURCE CODE LOGIC, "
                    "not manipulate the input data to make tests pass. "

                    "Return ONLY a valid JSON object with these keys: "
                    "root_cause, explanation, target_file, proposed_code. "

                    "target_file must be transactions.py. "
                    "proposed_code must contain the FULL corrected Python file. "

                    "STRICT RULES: "
                    "1. Preserve the original transactions list exactly. "
                    "2. Do not delete, reorder, or change transaction records. "
                    "3. Do not modify tests, fixtures, or expected values. "
                    "4. Fix duplicate handling inside calculate_total(). "
                    "5. Preserve public function names and signatures. "
                    "6. Do not include Markdown formatting. "
                    "7. Never claim that a repair is verified without tests."
                )
            }
        ]
    )

    content = response.choices[0].message.content

    # Parse the proposed repair
    patch = json.loads(content)

    required_keys = {
        "root_cause",
        "explanation",
        "target_file",
        "proposed_code"
    }

    if not required_keys.issubset(patch):
        raise ValueError("Model response is missing required fields.")

    if patch["target_file"] != "transactions.py":
        raise ValueError("Unexpected target file.")

    if not isinstance(patch["proposed_code"], str):
        raise ValueError("Proposed code must be a string.")

    # Check syntax without executing the generated code
    compile(patch["proposed_code"], "transactions.py", "exec")

    # Save the proposal; do NOT overwrite transactions.py
    Path("proposed_patch.json").write_text(
        json.dumps(patch, indent=2),
        encoding="utf-8"
    )

    return patch


if __name__ == "__main__":
    print("ROOTCAUSE AI - PATCH GENERATOR")
    print("=" * 40)

    patch = generate_patch()

    print("Suspected root cause:", patch["root_cause"])
    print("Proposed target:", patch["target_file"])
    print("Patch saved to proposed_patch.json")
    print("Status: NOT VERIFIED")
