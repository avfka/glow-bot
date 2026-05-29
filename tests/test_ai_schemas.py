import unittest

from services.ai_schemas import (
    ProductRecommendationsOutput,
    ProductScoreOutput,
    RoutineOutput,
    SkinAnalysisOutput,
)


class AISchemasTest(unittest.TestCase):
    def test_skin_analysis_defaults_and_filters_bad_steps(self):
        parsed = SkinAnalysisOutput.model_validate(
            {
                "skin_type": "oily",
                "problems": ["acne", 123, ""],
                "morning_routine": [
                    {"step": 1, "name": "Очищение", "product_type": "cleanser"},
                    "bad step",
                ],
                "evening_routine": "not a list",
                "recommended_ingredients": ["niacinamide", None],
                "confidence_score": 1.7,
                "skin_score": {"overall": 120, "hydration": "-10"},
            }
        )

        self.assertEqual(parsed.skin_type, "oily")
        self.assertEqual(parsed.problems, ["acne", "123"])
        self.assertEqual(len(parsed.morning_routine), 1)
        self.assertEqual(parsed.evening_routine, [])
        self.assertEqual(parsed.morning_steps()[0]["name"], "Очищение")
        self.assertEqual(parsed.recommended_ingredients, ["niacinamide"])
        self.assertEqual(parsed.confidence_score, 1)
        self.assertEqual(parsed.skin_score.overall, 100)
        self.assertEqual(parsed.skin_score.hydration, 0)

    def test_routine_output_uses_empty_defaults(self):
        parsed = RoutineOutput.model_validate({})

        self.assertEqual(parsed.morning_steps(), [])
        self.assertEqual(parsed.evening_steps(), [])
        self.assertEqual(parsed.recommended_ingredients, [])
        self.assertEqual(parsed.avoid_ingredients, [])

    def test_product_score_filters_bad_ingredient_notes(self):
        parsed = ProductScoreOutput.model_validate(
            {
                "score": 82,
                "suitable": True,
                "good_ingredients": [{"name": "Glycerin", "benefit": "hydration"}, {}],
                "bad_ingredients": ["bad"],
            }
        )

        self.assertEqual(parsed.score, 82)
        self.assertEqual(len(parsed.good_ingredients), 1)
        self.assertEqual(parsed.bad_ingredients, [])

    def test_score_bounds_are_clamped(self):
        self.assertEqual(ProductScoreOutput.model_validate({"score": 120}).score, 100)
        self.assertEqual(ProductScoreOutput.model_validate({"score": -1}).score, 0)

    def test_product_recommendations_filter_invalid_items(self):
        parsed = ProductRecommendationsOutput.model_validate(
            {
                "recommendations": [
                    {
                        "name": "Hydrating Cream",
                        "brand": "Brand",
                        "key_ingredients": ["glycerin", None, ""],
                        "time_of_use": "bad",
                    },
                    {"brand": "No name"},
                    "bad item",
                ]
            }
        )

        self.assertEqual(len(parsed.recommendations), 1)
        self.assertEqual(parsed.as_dicts()[0]["key_ingredients"], ["glycerin"])
        self.assertEqual(parsed.as_dicts()[0]["time_of_use"], "both")


if __name__ == "__main__":
    unittest.main()
