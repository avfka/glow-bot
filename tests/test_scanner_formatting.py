import unittest

from services.catalog_formatting import format_commerce_line


class ScannerFormattingTest(unittest.TestCase):
    def test_format_commerce_line_combines_price_rating_and_reviews(self):
        self.assertEqual(
            format_commerce_line(price=1299, rating=4.8, reviews_count=312),
            "Цена: 1299 ₽ | Рейтинг: 4.8 (312 отзывов)",
        )

    def test_format_commerce_line_skips_missing_values(self):
        self.assertEqual(format_commerce_line(price=990), "Цена: 990 ₽")
        self.assertEqual(format_commerce_line(), "")


if __name__ == "__main__":
    unittest.main()
