import ast
import unittest
from pathlib import Path


class ProductRecommendationBoundaryTest(unittest.TestCase):
    def test_product_search_handler_does_not_call_openai_directly(self):
        tree = ast.parse(
            Path("handlers/product_search.py").read_text(),
            filename="handlers/product_search.py",
        )
        offenders = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "openai":
                offenders.append(f"import:{node.lineno}")
            if isinstance(node, ast.Call) and _call_name(node) == "AsyncOpenAI":
                offenders.append(f"call:{node.lineno}")
            if isinstance(node, ast.Call) and _call_name(node) == "get_analyzer":
                offenders.append(f"get_analyzer:{node.lineno}")

        self.assertEqual(offenders, [])

    def test_product_search_handler_uses_recommendation_service(self):
        tree = ast.parse(
            Path("handlers/product_search.py").read_text(),
            filename="handlers/product_search.py",
        )

        calls_service = any(
            isinstance(node, ast.Call)
            and _call_name(node) == "get_product_recommendations"
            for node in ast.walk(tree)
        )

        self.assertTrue(calls_service)


def _call_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


if __name__ == "__main__":
    unittest.main()
