import ast
import unittest
from pathlib import Path


class ProductWorkflowBoundaryTest(unittest.TestCase):
    def test_product_handlers_do_not_generate_routines_directly(self):
        offenders = []
        for path in [Path("handlers/products.py"), Path("handlers/product_search.py")]:
            tree = ast.parse(path.read_text(), filename=str(path))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                if isinstance(node.func, ast.Attribute) and node.func.attr == "generate_routine":
                    offenders.append(f"{path}:{node.lineno}")

        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
