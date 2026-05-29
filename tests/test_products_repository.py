import ast
import unittest
from pathlib import Path


class ProductsRepositoryTest(unittest.TestCase):
    def test_catalog_search_matches_name_or_brand(self):
        tree = ast.parse(
            Path("database/repositories/products.py").read_text(),
            filename="database/repositories/products.py",
        )
        search_catalog = _find_function(tree, "search_catalog")

        self.assertTrue(_has_attribute(search_catalog, "ProductCatalog", "name"))
        self.assertTrue(_has_attribute(search_catalog, "ProductCatalog", "brand"))
        self.assertTrue(_calls_name(search_catalog, "or_"))
        self.assertTrue(_calls_attribute(search_catalog, "strip"))

    def test_catalog_upsert_supports_commerce_fields(self):
        tree = ast.parse(
            Path("database/repositories/products.py").read_text(),
            filename="database/repositories/products.py",
        )
        upsert = _find_function(tree, "upsert_catalog_product")

        self.assertTrue(_assigns_attribute(upsert, "price"))
        self.assertTrue(_assigns_attribute(upsert, "rating"))
        self.assertTrue(_assigns_attribute(upsert, "reviews_count"))
        self.assertTrue(_assigns_attribute(upsert, "review_summary"))


def _find_function(tree: ast.AST, name: str) -> ast.AsyncFunctionDef | ast.FunctionDef:
    for node in ast.walk(tree):
        if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)) and node.name == name:
            return node
    raise AssertionError(f"Function {name} not found")


def _has_attribute(node: ast.AST, root_name: str, attr_name: str) -> bool:
    return any(
        isinstance(child, ast.Attribute)
        and child.attr == attr_name
        and isinstance(child.value, ast.Name)
        and child.value.id == root_name
        for child in ast.walk(node)
    )


def _calls_name(node: ast.AST, name: str) -> bool:
    return any(
        isinstance(child, ast.Call)
        and isinstance(child.func, ast.Name)
        and child.func.id == name
        for child in ast.walk(node)
    )


def _calls_attribute(node: ast.AST, name: str) -> bool:
    return any(
        isinstance(child, ast.Call)
        and isinstance(child.func, ast.Attribute)
        and child.func.attr == name
        for child in ast.walk(node)
    )


def _assigns_attribute(node: ast.AST, attr_name: str) -> bool:
    return any(
        isinstance(child, ast.Assign)
        and any(
            isinstance(target, ast.Attribute) and target.attr == attr_name
            for target in child.targets
        )
        for child in ast.walk(node)
    )


if __name__ == "__main__":
    unittest.main()
