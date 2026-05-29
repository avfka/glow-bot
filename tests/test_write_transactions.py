import ast
import unittest
from pathlib import Path


WRITE_FUNCTIONS = {
    "add_catalog_product",
    "add_user_product",
    "check_and_grant_streak_achievements",
    "create_profile_version",
    "create_routine",
    "get_or_create_user",
    "increment_scan_count",
    "remove_user_product",
    "save_product_scan",
    "save_skin_analysis",
    "set_routine_product",
    "update_analysis_user_confirmation",
    "upsert_reminder",
    "upsert_tracking",
    "upsert_user_league",
}


class WriteTransactionBoundaryTest(unittest.TestCase):
    def test_write_calls_make_commit_boundary_explicit(self):
        missing = []
        for directory in ("handlers", "services"):
            for path in Path(directory).glob("*.py"):
                tree = ast.parse(path.read_text(), filename=str(path))
                for node in ast.walk(tree):
                    if not isinstance(node, ast.Call):
                        continue
                    name = _call_name(node)
                    if name not in WRITE_FUNCTIONS:
                        continue
                    if not any(keyword.arg == "commit" for keyword in node.keywords):
                        missing.append(f"{path}:{node.lineno}: {name}")

        self.assertEqual(missing, [])


def _call_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


if __name__ == "__main__":
    unittest.main()
