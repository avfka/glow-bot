import ast
import unittest
from pathlib import Path


FORBIDDEN_CALLS = {
    "add_catalog_product",
    "get_latest_profile",
    "increment_scan_count",
    "save_product_scan",
    "score_product",
    "search_catalog",
}


class ScannerWorkflowBoundaryTest(unittest.TestCase):
    def test_scanner_handler_does_not_call_db_or_scoring_directly(self):
        path = Path("handlers/scanner.py")
        tree = ast.parse(path.read_text(), filename=str(path))
        offenders = []

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = _call_name(node)
            if name in FORBIDDEN_CALLS:
                offenders.append(f"{path}:{node.lineno}: {name}")

        self.assertEqual(offenders, [])


def _call_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


if __name__ == "__main__":
    unittest.main()
