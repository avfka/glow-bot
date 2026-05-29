import ast
import unittest
from pathlib import Path


class UXNavigationTest(unittest.TestCase):
    def test_main_menu_prioritizes_core_user_actions(self):
        source = Path("utils/keyboards.py").read_text()

        self.assertIn("🔍 Сканер состава", source)
        self.assertIn("🧴 Мои продукты", source)
        self.assertIn("⚙️ Настройки", source)
        self.assertIn('KeyboardButton("🏆 Лидерборд")', source)
        self.assertIn('callback_data="search:start"', source)

    def test_product_search_has_inline_entry_point(self):
        tree = ast.parse(Path("handlers/product_search.py").read_text())

        self.assertTrue(
            any(
                isinstance(node, ast.Call)
                and _call_name(node) == "CallbackQueryHandler"
                and any(
                    keyword.arg == "pattern"
                    and isinstance(keyword.value, ast.Constant)
                    and keyword.value.value == "^search:start$"
                    for keyword in node.keywords
                )
                for node in ast.walk(tree)
            )
        )

    def test_onboarding_start_callback_is_entry_point(self):
        tree = ast.parse(Path("handlers/onboarding.py").read_text())
        get_handler = _find_function(tree, "get_onboarding_handler")
        entry_points = _keyword_value(get_handler, "entry_points")

        self.assertIsNotNone(entry_points)
        self.assertTrue(
            any(
                isinstance(node, ast.Call)
                and _call_name(node) == "CallbackQueryHandler"
                and any(
                    keyword.arg == "pattern"
                    and isinstance(keyword.value, ast.Constant)
                    and keyword.value.value == "^onboarding:start$"
                    for keyword in node.keywords
                )
                for node in ast.walk(entry_points)
            )
        )

    def test_settings_profile_callback_has_handler(self):
        tree = ast.parse(Path("handlers/settings.py").read_text())

        self.assertTrue(_function_exists(tree, "btn_settings_profile"))
        self.assertTrue(
            any(
                isinstance(node, ast.Call)
                and _call_name(node) == "CallbackQueryHandler"
                and any(
                    keyword.arg == "pattern"
                    and isinstance(keyword.value, ast.Constant)
                    and keyword.value.value == "^settings:profile$"
                    for keyword in node.keywords
                )
                for node in ast.walk(tree)
            )
        )

    def test_onboarding_no_longer_collects_reminder_times_before_analysis(self):
        source = Path("handlers/onboarding.py").read_text()

        self.assertNotIn("WAIT_MORNING_TIME", source)
        self.assertNotIn("WAIT_EVENING_TIME", source)
        self.assertNotIn("WAIT_TIMEZONE", source)
        self.assertIn("routine_ready_keyboard", source)

    def test_recovery_keyboards_are_available_in_long_flows(self):
        keyboards = Path("utils/keyboards.py").read_text()
        scanner = Path("handlers/scanner.py").read_text()
        products = Path("handlers/products.py").read_text()
        search = Path("handlers/product_search.py").read_text()
        settings = Path("handlers/settings.py").read_text()

        self.assertIn("cancel_flow_keyboard", keyboards)
        self.assertIn("scan_retry_keyboard", keyboards)
        self.assertIn("product_search_empty_keyboard", keyboards)
        self.assertIn("cancel:scan", scanner)
        self.assertIn("cancel:products", products)
        self.assertIn("cancel:search", search)
        self.assertIn("cancel:settings", settings)


def _find_function(tree: ast.AST, name: str) -> ast.FunctionDef | ast.AsyncFunctionDef:
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    raise AssertionError(f"Function {name} not found")


def _function_exists(tree: ast.AST, name: str) -> bool:
    try:
        _find_function(tree, name)
        return True
    except AssertionError:
        return False


def _keyword_value(node: ast.AST, name: str) -> ast.AST | None:
    for child in ast.walk(node):
        if not isinstance(child, ast.Call) or _call_name(child) != "ConversationHandler":
            continue
        for keyword in child.keywords:
            if keyword.arg == name:
                return keyword.value
    return None


def _call_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


if __name__ == "__main__":
    unittest.main()
