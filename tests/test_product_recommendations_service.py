import unittest
from types import SimpleNamespace

from services.product_recommendations import build_recommendation_prompt


class ProductRecommendationsServiceTest(unittest.TestCase):
    def test_build_recommendation_prompt_uses_profile_fields(self):
        profile = SimpleNamespace(
            skin_type="oily",
            skin_problems=["acne"],
            budget="low",
            goal="hydration",
            allergies="fragrance",
        )

        prompt = build_recommendation_prompt(profile, "Сыворотка")

        self.assertIn("Сыворотка", prompt)
        self.assertIn("жирная", prompt)
        self.assertIn("acne", prompt)
        self.assertIn("до 500", prompt)
        self.assertIn("fragrance", prompt)


if __name__ == "__main__":
    unittest.main()
