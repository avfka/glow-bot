import ast
import unittest
from pathlib import Path

from utils.logging import redact_sensitive_text


class LoggingRedactionTest(unittest.TestCase):
    def test_redacts_telegram_bot_url_token(self):
        text = (
            "POST https://api.telegram.org/bot123456:ABC_def-ghi/getUpdates "
            '"HTTP/1.1 200 OK"'
        )

        redacted = redact_sensitive_text(text)

        self.assertNotIn("123456:ABC_def-ghi", redacted)
        self.assertIn("/bot<redacted>/getUpdates", redacted)

    def test_redacts_exact_secret(self):
        redacted = redact_sensitive_text(
            "token=secret-token-value",
            ["secret-token-value"],
        )

        self.assertEqual(redacted, "token=<redacted>")

    def test_bot_configures_redacted_logging(self):
        tree = ast.parse(Path("bot.py").read_text(), filename="bot.py")

        self.assertTrue(
            any(
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "configure_logging"
                for node in ast.walk(tree)
            )
        )


if __name__ == "__main__":
    unittest.main()
