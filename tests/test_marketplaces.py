import unittest
from pathlib import Path

from utils.marketplaces import marketplace_search_urls, merge_marketplace_urls


class MarketplacesTest(unittest.TestCase):
    def test_marketplace_search_urls_include_core_russian_shops(self):
        urls = marketplace_search_urls("La Roche Posay крем")

        self.assertIn("wildberries.ru", urls["wb"])
        self.assertIn("ozon.ru", urls["ozon"])
        self.assertIn("goldapple.ru", urls["goldapple"])
        self.assertIn("La+Roche+Posay", urls["wb"])

    def test_marketplace_search_urls_skip_blank_product_name(self):
        self.assertEqual(marketplace_search_urls("   "), {})

    def test_merge_marketplace_urls_prefers_catalog_urls_when_available(self):
        urls = merge_marketplace_urls(
            "Bioderma Sensibio",
            wb_url="https://www.wildberries.ru/catalog/123/detail.aspx",
            za_url="https://goldapple.ru/19000000001-sensibio",
        )

        self.assertEqual(urls["wb"], "https://www.wildberries.ru/catalog/123/detail.aspx")
        self.assertEqual(urls["goldapple"], "https://goldapple.ru/19000000001-sensibio")
        self.assertIn("ozon.ru", urls["ozon"])

    def test_keyboards_show_marketplace_alternatives(self):
        source = Path("utils/keyboards.py").read_text()

        self.assertIn('InlineKeyboardButton("WB"', source)
        self.assertIn('InlineKeyboardButton("Ozon"', source)
        self.assertIn('InlineKeyboardButton("ЗЯ"', source)


if __name__ == "__main__":
    unittest.main()
