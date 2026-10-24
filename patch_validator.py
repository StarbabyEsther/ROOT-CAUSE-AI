
import ast
import json
from pathlib import Path


def validate_patch(source_file="transactions.py"):
    original_code = Path(source_file).read_text(
        encoding="utf-8"
    )

    patch = json.loads(
        Path("proposed_patch.json").read_text(
            encoding="utf-8"
        )
    )

    if patch.get("target_file") != source_file:
        return False, "Unauthorized target file."

    proposed_code = patch.get("proposed_code")

    if not isinstance(proposed_code, str):
        return False, "Proposed code is missing or invalid."

    try:
        original_tree = ast.parse(original_code)
        proposed_tree = ast.parse(proposed_code)
    except SyntaxError as error:
        return False, f"Python syntax error: {error}"

    # The AI may only propose one function.
    if (
        len(proposed_tree.body) != 1
        or not isinstance(proposed_tree.body[0], ast.FunctionDef)
        or proposed_tree.body[0].name != "calculate_total"
    ):
        return False, "Patch must contain only calculate_total()."

    proposed_function = proposed_tree.body[0]

    # Find the original calculate_total function.
    original_function = next(
        (
            node for node in original_tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "calculate_total"
        ),
        None
    )

    if original_function is None:
        return False, "Original calculate_total() not found."

    # Preserve the original function signature.
    if ast.dump(original_function.args) != ast.dump(
        proposed_function.args
    ):
        return False, "Function signature was modified."

    # Prevent code from being executed in default argument values
    # or decorators during function definition.
    if proposed_function.decorator_list:
        return False, "Decorators are not allowed."

    if (
        proposed_function.args.defaults
        or any(
            value is not None
            for value in proposed_function.args.kw_defaults
        )
    ):
        return False, "Default parameter values are not allowed."

    # No automatic application or execution occurs here.
    return True, "Structural validation passed; NOT VERIFIED."


if __name__ == "__main__":
    valid, reason = validate_patch()

    print("ROOTCAUSE AI - PATCH VALIDATOR")
    print("=" * 40)
    print("Valid:", valid)
    print("Reason:", reason)
