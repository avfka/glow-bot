import unittest
from datetime import time

from services.onboarding import parse_time


class ParseTimeTest(unittest.TestCase):
    def test_parses_hh_mm(self):
        self.assertEqual(parse_time("08:30"), time(8, 30))

    def test_returns_none_for_empty_value(self):
        self.assertIsNone(parse_time(None))
        self.assertIsNone(parse_time(""))

    def test_returns_none_for_invalid_value(self):
        self.assertIsNone(parse_time("8"))
        self.assertIsNone(parse_time("bad"))
        self.assertIsNone(parse_time("25:00"))


if __name__ == "__main__":
    unittest.main()
