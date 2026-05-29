import unittest

from services.catalog_import import parse_float, parse_int


class CatalogImportTest(unittest.TestCase):
    def test_parse_int_handles_prices_and_counts(self):
        self.assertEqual(parse_int("1 299 ₽"), 1299)
        self.assertEqual(parse_int("12 отзывов"), 12)
        self.assertIsNone(parse_int(""))

    def test_parse_float_handles_comma_rating(self):
        self.assertEqual(parse_float("4,8"), 4.8)
        self.assertEqual(parse_float("4.5"), 4.5)
        self.assertIsNone(parse_float("нет"))


if __name__ == "__main__":
    unittest.main()
