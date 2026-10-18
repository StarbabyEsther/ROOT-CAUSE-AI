
import ast
import json
from pathlib import Path


def validate_patch():
    original_code = Path("transactions.py").read_text(
        encoding="utf-8"
    )

    patch = json.loads(
        Path("proposed_patch.json").read_text(
            encoding="utf-8"
        )
    )

    if patch.get("target_file") != "transactions.py":
        return False, "Patch targets an unauthorized file."

    proposed_code = patch.get("proposed_code")

    if not isinstance(proposed_code, str):
        return False, "Proposed code is missing or invalid."

    try:
        original_tree = ast.parse(original_code)
        proposed_tree = ast.parse(proposed_code)
    except SyntaxError as error:
        return False, f"Invalid Python syntax: {error}"

    def get_transactions_definition(tree):
        for node in tree.body:
            if isinstance(node, ast.Assign):
                if any(
                    isinstance(target, ast.Name)
                    and target.id == "transactions"
                    for target in node.targets
                ):
                    return ast.dump(node.value)

        return None

    original_data = get_transactions_definition(original_tree)
    proposed_data = get_transactions_definition(proposed_tree)

    if original_data is None or proposed_data != original_data:
        return False, "Original transaction records were modified."

    original_functions = {
        node.name
        for node in original_tree.body
        if isinstance(node, ast.FunctionDef)
    }

    proposed_functions = {
        node.name
        for node in proposed_tree.body
        if isinstance(node, ast.FunctionDef)
    }

    if not original_functions.issubset(proposed_functions):
        return False, "An original function was removed."

    original_calculate = next(
        node for node in original_tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "calculate_total"
    )

    proposed_calculate = next(
        (
            node for node in proposed_tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "calculate_total"
        ),
        None
    )

    if proposed_calculate is None:
        return False, "calculate_total() was removed."

    if ast.dump(original_calculate.args) != ast.dump(
        proposed_calculate.args
    ):
        return False, "calculate_total() signature was changed."

    # Disallow unexpected top-level statements, including
    # new imports and executable calls.
    allowed_nodes = (
        ast.FunctionDef,
        ast.Assign,
        ast.If,
        ast.Expr
    )

    if any(
        not isinstance(node, allowed_nodes)
        for node in proposed_tree.body
    ):
        return False, "Unexpected top-level code found."

    return True, "Structural checks passed; patch is NOT verified."


if __name__ == "__main__":
    valid, message = validate_patch()

    print("ROOTCAUSE AI - PATCH VALIDATOR")
    print("=" * 40)
    print("Valid:", valid)
    print("Reason:", message)
