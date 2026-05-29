import ast
import unittest
from pathlib import Path

from utils.admin import is_super_admin, parse_admin_ids


class AdminAccessTest(unittest.TestCase):
    def test_parse_admin_ids_accepts_commas_and_semicolons(self):
        self.assertEqual(parse_admin_ids("1, 2;bad,3"), {1, 2, 3})

    def test_is_super_admin_requires_configured_id(self):
        self.assertTrue(is_super_admin(42, "1,42"))
        self.assertFalse(is_super_admin(7, "1,42"))
        self.assertFalse(is_super_admin(None, "1,42"))

    def test_bot_registers_admin_handlers(self):
        tree = ast.parse(Path("bot.py").read_text(), filename="bot.py")
        self.assertTrue(_calls_name(tree, "get_admin_handlers"))

    def test_admin_set_profile_uses_allowlist_and_creates_profile_version(self):
        tree = ast.parse(Path("handlers/admin.py").read_text(), filename="handlers/admin.py")

        self.assertTrue(_has_name(tree, "EDITABLE_PROFILE_FIELDS"))
        self.assertTrue(_calls_name(tree, "create_profile_version"))
        self.assertTrue(_calls_name(tree, "is_super_admin"))


def _calls_name(node: ast.AST, name: str) -> bool:
    return any(
        isinstance(child, ast.Call)
        and isinstance(child.func, ast.Name)
        and child.func.id == name
        for child in ast.walk(node)
    )


def _has_name(node: ast.AST, name: str) -> bool:
    return any(isinstance(child, ast.Name) and child.id == name for child in ast.walk(node))


if __name__ == "__main__":
    unittest.main()
