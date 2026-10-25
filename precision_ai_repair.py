
import ast
import json
import re
import subprocess
from pathlib import Path

from patch_generator import client, MODEL_ID

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "precision_processor.py"
TESTS = ROOT / "test_precision_processor.py"
BUNDLE = ROOT / "precision_verification_bundle"

MAX_ATTEMPTS = 2


def run_tests(source_path):
    command = [
        "contree", "run",
        "--use", "tag:python:3.12-slim",
        "--file", f"{source_path}:/app/precision_processor.py",
        "--file", f"{TESTS}:/app/test_precision_processor.py",
        "--disposable",
        "--",
        "python", "-m", "unittest", "discover",
        "-s", "/app", "-p", "test_precision_processor.py", "-v",
    ]

    result = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=240,
        check=False,
    )

    logs = result.stdout + "\n" + result.stderr

    def extract(pattern):
        match = re.search(pattern, logs)
        return int(match.group(1)) if match else 0

    ran = extract(r"Ran (\d+) tests?")
    failures = extract(r"failures=(\d+)")
    errors = extract(r"errors=(\d+)")

    passed = (
        result.returncode == 0
        and ran == 5
        and re.search(r"(?m)^OK\s*$", logs) is not None
    )

    return {
        "passed": passed,
        "ran": ran,
        "failures": failures,
        "errors": errors,
        "logs": logs,
    }


def build_repaired_copy(original, proposed):
    old_tree = ast.parse(original)
    new_tree = ast.parse(proposed)

    old_functions = [
        node for node in old_tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "calculate_total"
    ]

    if len(old_functions) != 1:
        raise ValueError("Original calculate_total() not found.")

    if (
        len(new_tree.body) != 1
        or not isinstance(new_tree.body[0], ast.FunctionDef)
        or new_tree.body[0].name != "calculate_total"
    ):
        raise ValueError("Patch must contain only calculate_total().")

    old_fn = old_functions[0]
    new_fn = new_tree.body[0]

    if ast.dump(old_fn.args) != ast.dump(new_fn.args):
        raise ValueError("Function signature was modified.")

    if new_fn.decorator_list or new_fn.args.defaults:
        raise ValueError("Decorators and defaults are not permitted.")

    lines = original.splitlines(keepends=True)

    repaired = (
        "".join(lines[:old_fn.lineno - 1])
        + proposed.rstrip()
        + "\n"
        + "".join(lines[old_fn.end_lineno:])
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

    if protected_nodes(old_tree) != protected_nodes(repaired_tree):
        raise ValueError("Protected code was changed.")

    return repaired


def repair_precision():
    print("ROOTCAUSE AI - MONETARY PRECISION REPAIR")
    print("=" * 45)

    original = SOURCE.read_text(encoding="utf-8")

    print("\nRunning original tests in Nebius Sandbox...")
    baseline = run_tests(SOURCE)

    print("Baseline failures:", baseline["failures"])

    if (
        baseline["ran"] != 5
        or baseline["failures"] != 4
        or baseline["errors"] != 0
    ):
        print("Unexpected baseline. Repair stopped.")
        print(baseline["logs"])
        return

    feedback = "No previous attempt."

    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f"\nNemotron repair attempt {attempt}/2")

        try:
            response = client.chat.completions.create(
                model=MODEL_ID,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert Python financial software "
                            "repair agent. Return exactly one JSON object "
                            "with keys root_cause, explanation, target_file, "
                            "and proposed_code. "
                            "target_file must be precision_processor.py. "
                            "proposed_code must contain ONLY the complete "
                            "calculate_total(transactions) function. "
                            "Fix floating-point financial inaccuracies. "
                            "Use Python decimal.Decimal and convert amounts "
                            "using Decimal(str(amount)). "
                            "You may place imports inside calculate_total. "
                            "Preserve payment and refund behavior. "
                            "Do not modify records or test expectations. "
                            "Return no Markdown or extra text."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            "Repair this monetary precision bug.\n\n"
                            "ORIGINAL CODE:\n"
                            + original
                            + "\n\nEXPECTED BEHAVIOR:\n"
                            "Exact decimal arithmetic for payments and "
                            "refunds, including 0.1 + 0.2 == 0.3.\n\n"
                            "PREVIOUS FEEDBACK:\n"
                            + feedback
                        ),
                    },
                ],
            )

            patch = json.loads(response.choices[0].message.content)

            if not isinstance(patch, dict):
                raise ValueError("Expected a JSON object.")

            if patch.get("target_file") != "precision_processor.py":
                raise ValueError("Unauthorized target file.")

            proposed = patch.get("proposed_code")

            if not isinstance(proposed, str) or not proposed.strip():
                raise ValueError("Missing proposed function.")

            repaired = build_repaired_copy(original, proposed)

            BUNDLE.mkdir(exist_ok=True)

            repaired_file = BUNDLE / "precision_processor.py"
            repaired_file.write_text(repaired, encoding="utf-8")

            print("Structural validation: PASSED")
            print("Testing AI repair in Nebius Sandbox...")

            result = run_tests(repaired_file)

            verdict = (
                "verified_fixed" if result["passed"] else "not_fixed"
            )

            report = {
                "scenario_id": "monetary_precision",
                "attempts": attempt,
                "baseline_failed": baseline["failures"],
                "final_passed": result["ran"] if result["passed"] else
                    max(0, result["ran"] - result["failures"] - result["errors"]),
                "final_failed": result["failures"] + result["errors"],
                "verdict": verdict,
                "logs": result["logs"],
            }

            (ROOT / "precision_verification_report.json").write_text(
                json.dumps(report, indent=2),
                encoding="utf-8",
            )

            (ROOT / "precision_proposed_patch.json").write_text(
                json.dumps(patch, indent=2),
                encoding="utf-8",
            )

            print("Final verdict:", verdict)
            print("Tests executed:", result["ran"])

            if result["passed"]:
                print("Tests passed: 5/5")
                print("MONETARY PRECISION REPAIR VERIFIED!")
                return

            feedback = "Sandbox test failure:\n" + result["logs"][-2000:]

        except Exception as error:
            print("Attempt rejected:", error)
            feedback = str(error)

    print("\nNo verified repair after two attempts.")


if __name__ == "__main__":
    repair_precision()
