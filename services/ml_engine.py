"""Stub for future in-house ML skin analysis engine."""
from typing import Optional

from services.skin_analyzer import SkinAnalyzer, SkinAnalysisResult


class MLEngineAnalyzer(SkinAnalyzer):
    """Placeholder — replace with real ML model when ready."""

    async def analyze_skin(
        self,
        photo_base64: Optional[str],
        skin_type: str,
        problems: list[str],
        allergies: Optional[str],
        budget: str,
        goal: str,
        age: int,
    ) -> SkinAnalysisResult:
        raise NotImplementedError("ML engine is not implemented yet")

    async def generate_routine(
        self,
        profile: dict,
        user_products: list[dict],
    ) -> SkinAnalysisResult:
        raise NotImplementedError("ML engine is not implemented yet")

    async def extract_ingredients_from_image(self, photo_base64: str) -> str:
        raise NotImplementedError("ML engine is not implemented yet")
