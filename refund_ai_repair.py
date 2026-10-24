
import ast
import json
import re
import subprocess
from pathlib import Path

from patch_generator import client, MODEL_ID
from financial_investigator import investigate_transactions
from refund_processor import transactions, calculate_total

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "refund_processor.py"
TESTS = ROOT / "test_refund_processor.py"
BUNDLE = ROOT / "refund_verification_bundle"
EXPECTED_TEST_COUNT = 7


def run_sandbox_tests(source_path):
    command = [
        "contree", "run",
        "--use", "tag:python:3.12-slim",
        "--file", f"./{source_path}:/app/refund_processor.py",
        "--file", "./test_refund_processor.py:/app/test_refund_processor.py",
        "--disposable",
        "--",
        "python", "-m", "unittest", "discover",
        "-s", "/app",
        "-p", "test_refund_processor.py",
        "-v",
    ]

    result = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=240,
        check=False,
    )

    output = result.stdout + "\n" + result.stderr

    def count(pattern):
        match = re.search(pattern, output)
        return int(match.group(1)) if match else 0

    ran = count(r"Ran (\d+) tests?")
    failures = count(r"failures=(\d+)")
    errors = count(r"errors=(\d+)")

    passed = (
        result.returncode == 0
        and ran == EXPECTED_TEST_COUNT
        and re.search(r"(?m)^OK\s*$", output) is not None
    )

    return {
        "passed": passed,
        "ran": ran,
        "failures": failures,
        "errors": errors,
        "logs": output,
    }


def prepare_repair(original, proposed):
              
    original_tree = ast.parse(original)
    proposed_tree = ast.parse(proposed)

    originals = [
        node for node in original_tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "calculate_total"
    ]

    if len(originals) != 1:
        raise ValueError("Expected one original calculate_total function.")

    if (
        len(proposed_tree.body) != 1
        or not isinstance(proposed_tree.body[0], ast.FunctionDef)
        or proposed_tree.body[0].name != "calculate_total"
    ):
        raise ValueError("AI must return only calculate_total().")

    old_function = originals[0]
    new_function = proposed_tree.body[0]

    if ast.dump(old_function.args) != ast.dump(new_function.args):
        raise ValueError("Function signature changed.")

    if new_function.decorator_list:
        raise ValueError("Decorators are not permitted.")

    lines = original.splitlines(keepends=True)

    repaired = (
        "".join(lines[:old_function.lineno - 1])
        + proposed.rstrip()
        + "\n"
        + "".join(lines[old_function.end_lineno:])
    )

    repaired_tree = ast.parse(repaired)

    def protected_nodes(tree):
        return [
            ast.dump(node, include_attributes=False)
            for node in tree.body
            if not (
                isinstance(node, ast.FunctionDef)
                and node.name == "calculate_total"
            )
        ]

    if protected_nodes(original_tree) != protected_nodes(repaired_tree):
        raise ValueError("Patch modified protected source code.")

    return repaired


def repair_refund():
    print("ROOTCAUSE AI - REFUND REPAIR AGENT")
    print("=" * 45)

    original = SOURCE.read_text(encoding="utf-8")

    if not TESTS.exists():
        raise FileNotFoundError("Refund regression tests are missing.")

    report = investigate_transactions(
        transactions,
        calculator=calculate_total,
    )

    print("Issue:", report["issue_type"])
    print("Discrepancy: $", report["discrepancy"])

    print("\nRunning original tests in Nebius Sandbox...")
    baseline = run_sandbox_tests("refund_processor.py")

    print("Baseline failures:", baseline["failures"])

    if (
        baseline["ran"] != EXPECTED_TEST_COUNT
        or baseline["failures"] != 3
        or baseline["errors"] != 0
    ):
        print("Unexpected baseline. Repair stopped.")
        print(baseline["logs"])
        return

    feedback = "No previous attempt."

    for attempt in range(1, 3):
        print(f"\nNemotron repair attempt {attempt}/2")

        try:
            response = client.chat.completions.create(
                model=MODEL_ID,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You repair financial Python software. "
                            "Return exactly one valid JSON object with "
                            "root_cause, explanation, target_file, "
                            "and proposed_code. "
                            "target_file must be refund_processor.py. "
                            "proposed_code must contain ONLY the "
                            "corrected calculate_total(transactions) "
                            "function, not the complete file. "
                            "Return proposed_code as a JSON string containing "
                            "valid Python source code. "
                            "Use standard JSON escaping for newlines. "
                            "Do not include Markdown code fences or literal "
                            "backslash-n sequences in the decoded Python code. "
                            "Fix incorrect refund calculations. "
                            "Payments must be added and refunds "
                            "must be subtracted. "
                            "Preserve all original transaction data. "
                            "Do not modify tests or expected values. "
                            "No Markdown or extra text."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            "Financial investigation:\n"
                            + json.dumps(report)
                            + "\n\nOriginal source:\n"
                            + original
                            + "\n\nPrevious feedback:\n"
                            + feedback
                        ),
                    },
                ],
            )

            patch = json.loads(
                response.choices[0].message.content
            )

            if not isinstance(patch, dict):
                raise ValueError("Response is not a JSON object.")

            if patch.get("target_file") != "refund_processor.py":
                raise ValueError("Unauthorized target file.")

            proposed = patch.get("proposed_code")

            if not isinstance(proposed, str) or not proposed.strip():
                raise ValueError("Missing proposed Python code.")

            try:
                repaired = prepare_repair(original, proposed)

            except SyntaxError as error:
                raise ValueError(
                    f"Nemotron generated invalid Python code: {error}"
                    f"Problematic line: {error.text!r}"
                ) from error
            
            (ROOT / "refund_proposed_patch.json").write_text(
                json.dumps(patch, indent=2),
                encoding="utf-8"
            )
            BUNDLE.mkdir(exist_ok=True)
            (BUNDLE / "refund_processor.py").write_text(
                repaired,
                encoding="utf-8",
            )

            print("Patch passed structural validation.")
            print("Running repair inside Nebius Sandbox...")

            result = run_sandbox_tests(
                "refund_verification_bundle/refund_processor.py"
            )

            verdict = (
                "verified_fixed"
                if result["passed"]
                else "not_fixed"
            )

            verification = {
                "scenario_id": "refund_sign_error",
                "attempts": attempt,
                "baseline_failed": baseline["failures"],
                "final_passed": (
                    result["ran"]
                    - result["failures"]
                    - result["errors"]
                ) if result["passed"] else 0,
                "final_failed": result["failures"] + result["errors"],
                "verdict": verdict,
                "logs": result["logs"],
            }

            (ROOT / "refund_verification_report.json").write_text(
                json.dumps(verification, indent=2),
                encoding="utf-8",
            )

            print("Final verdict:", verdict)
            print("Tests executed:", result["ran"])

            if result["passed"]:
                print("Passed:", result["ran"])
                print("REFUND REPAIR VERIFIED!")
                return

            feedback = (
                "The previous repair failed sandbox tests:\n"
                + result["logs"][-2500:]
            )

        except Exception as error:
            feedback = str(error)
            print("Attempt rejected:", error)

    print("\nNo verified refund repair after two attempts.")


if __name__ == "__main__":
    repair_refund()
