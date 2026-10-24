
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


def generate_patch(feedback=None):
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
                    "You are RootCause AI, an expert Python software "
                    "repair agent specializing in financial applications. "

                    "Return exactly ONE valid JSON object containing "
                    "these four keys: root_cause, explanation, "
                    "target_file, proposed_code. "

                    "target_file must be transactions.py. "

                    "IMPORTANT: proposed_code must contain ONLY "
                    "the complete corrected calculate_total() function. "
                    "Do NOT generate the entire Python file. "
                    "Do NOT include the transactions list. "
                    "Do NOT include imports, examples, or other functions. "

                    "Preserve the function name calculate_total "
                    "and its parameter transactions. "

                    "Repair duplicate transaction handling using "
                    "a set of previously processed transaction IDs. "
                    "Process each unique transaction ID only once. "

                    "Preserve the original payment and refund rules: "
                    "Payment amounts must be added. "
                    "Refund amounts must be subtracted. "

                    "Do not change financial records or test expectations. "
                    "Do not include Markdown code fences. "
                    "Do not add explanations outside the JSON object. "
                    "Never claim the generated patch is verified."
                )
            }
,
            {
                "role": "user",
                "content": (
                    "Repair this financial software bug.\n\n"
                    "FINANCIAL REPORT:\n"
                    + json.dumps(report, indent=2)
                    + "\n\nORIGINAL SOURCE CODE:\n"
                    + source_code
                    + "\n\nPREVIOUS VALIDATION FEEDBACK:\n"
                    + (feedback if feedback else "No previous attempt.")
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
    import ast

    tree = ast.parse(patch["proposed_code"])

    if (
        len(tree.body) != 1
        or not isinstance(tree.body[0], ast.FunctionDef)
        or tree.body[0].name != "calculate_total"
    ):
        raise ValueError(
            "Patch must contain only calculate_total()."
        )
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
