from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SkinAnalysisResult:
    skin_type: str
    problems: list[str] = field(default_factory=list)
    recommended_ingredients: list[str] = field(default_factory=list)
    avoid_ingredients: list[str] = field(default_factory=list)
    morning_routine: list[dict] = field(default_factory=list)
    evening_routine: list[dict] = field(default_factory=list)
    confidence_score: float = 0.0
    raw_response: Optional[dict] = None


class SkinAnalyzer(ABC):
    """Abstract interface for skin analysis backends."""

    @abstractmethod
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
        """Analyse skin from photo + profile and return standardised result."""
        ...

    @abstractmethod
    async def generate_routine(
        self,
        profile: dict,
        user_products: list[dict],
    ) -> SkinAnalysisResult:
        """Generate / update skincare routine based on profile and owned products."""
        ...

    @abstractmethod
    async def extract_ingredients_from_image(self, photo_base64: str) -> str:
        """OCR — extract INCI ingredient list from a product photo."""
        ...
