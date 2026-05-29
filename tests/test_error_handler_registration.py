import ast
import unittest
from pathlib import Path


class ErrorHandlerRegistrationTest(unittest.TestCase):
    def test_bot_registers_central_error_handler(self):
        tree = ast.parse(Path("bot.py").read_text(), filename="bot.py")
        registered = False

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr != "add_error_handler":
                continue
            if node.args and isinstance(node.args[0], ast.Name) and node.args[0].id == "handle_error":
                registered = True

        self.assertTrue(registered)


if __name__ == "__main__":
    unittest.main()
