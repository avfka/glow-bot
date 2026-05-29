import ast
import unittest
from pathlib import Path


class StaleCallbackGuardTest(unittest.TestCase):
    def test_product_callbacks_guard_missing_product_session(self):
        tree = ast.parse(Path("handlers/products.py").read_text(), filename="handlers/products.py")

        choose_type = _find_function(tree, "choose_product_type")
        choose_time = _find_function(tree, "choose_product_time")

        self.assertTrue(_contains_user_data_get(choose_type, "new_product"))
        self.assertTrue(_contains_conversation_end(choose_type))
        self.assertTrue(_contains_user_data_pop_default_none(choose_time, "new_product"))
        self.assertTrue(_contains_conversation_end(choose_time))

    def test_product_search_callbacks_validate_cached_recommendation_index(self):
        tree = ast.parse(
            Path("handlers/product_search.py").read_text(),
            filename="handlers/product_search.py",
        )

        pick = _find_function(tree, "btn_pick_recommendation")
        add = _find_function(tree, "btn_add_to_routine")

        self.assertTrue(_calls_function(pick, "_parse_callback_index"))
        self.assertTrue(_calls_function(add, "_parse_callback_index"))
        self.assertTrue(_function_exists(tree, "_parse_callback_index"))

    def test_settings_callbacks_guard_missing_reminder_session(self):
        tree = ast.parse(Path("handlers/settings.py").read_text(), filename="handlers/settings.py")

        receive_evening = _find_function(tree, "receive_evening_reminder")
        skip_evening = _find_function(tree, "skip_evening_reminder")
        choose_tz = _find_function(tree, "choose_reminder_tz")

        self.assertTrue(_contains_user_data_get(receive_evening, "new_reminder"))
        self.assertTrue(_contains_user_data_get(skip_evening, "new_reminder"))
        self.assertTrue(_contains_user_data_pop_default_none(choose_tz, "new_reminder"))
        self.assertTrue(_contains_conversation_end(choose_tz))


def _find_function(tree: ast.AST, name: str) -> ast.AsyncFunctionDef | ast.FunctionDef:
    for node in ast.walk(tree):
        if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)) and node.name == name:
            return node
    raise AssertionError(f"Function {name} not found")


def _function_exists(tree: ast.AST, name: str) -> bool:
    try:
        _find_function(tree, name)
        return True
    except AssertionError:
        return False


def _calls_function(node: ast.AST, name: str) -> bool:
    return any(
        isinstance(child, ast.Call)
        and isinstance(child.func, ast.Name)
        and child.func.id == name
        for child in ast.walk(node)
    )


def _contains_user_data_get(node: ast.AST, key: str) -> bool:
    return _contains_user_data_call(node, "get", key)


def _contains_user_data_pop_default_none(node: ast.AST, key: str) -> bool:
    for child in ast.walk(node):
        if not _is_user_data_method_call(child, "pop", key):
            continue
        if len(child.args) >= 2 and isinstance(child.args[1], ast.Constant) and child.args[1].value is None:
            return True
    return False


def _contains_user_data_call(node: ast.AST, method: str, key: str) -> bool:
    return any(_is_user_data_method_call(child, method, key) for child in ast.walk(node))


def _is_user_data_method_call(node: ast.AST, method: str, key: str) -> bool:
    if not isinstance(node, ast.Call):
        return False
    if not isinstance(node.func, ast.Attribute) or node.func.attr != method:
        return False
    receiver = node.func.value
    if not (
        isinstance(receiver, ast.Attribute)
        and receiver.attr == "user_data"
        and isinstance(receiver.value, ast.Name)
        and receiver.value.id == "context"
    ):
        return False
    return bool(node.args and isinstance(node.args[0], ast.Constant) and node.args[0].value == key)


def _contains_conversation_end(node: ast.AST) -> bool:
    for child in ast.walk(node):
        if not isinstance(child, ast.Return):
            continue
        value = child.value
        if (
            isinstance(value, ast.Attribute)
            and value.attr == "END"
            and isinstance(value.value, ast.Name)
            and value.value.id == "ConversationHandler"
        ):
            return True
    return False


if __name__ == "__main__":
    unittest.main()
