from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _clamp_number(value: Any, default: float, minimum: float, maximum: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return min(max(number, minimum), maximum)


class RoutineStep(BaseModel):
    model_config = ConfigDict(extra="ignore")

    step: int = Field(default=1, ge=1)
    name: str = "Шаг ухода"
    description: str = ""
    product_type: str = "other"


class SkinScore(BaseModel):
    model_config = ConfigDict(extra="ignore")

    overall: int | None = None
    hydration: int | None = None
    evenness: int | None = None
    pores: int | None = None

    @field_validator("overall", "hydration", "evenness", "pores", mode="before")
    @classmethod
    def _score(cls, value: Any) -> int | None:
        if value is None:
            return None
        return int(_clamp_number(value, 0, 0, 100))


class RoutineOutput(BaseModel):
    model_config = ConfigDict(extra="ignore")

    morning_routine: list[RoutineStep] = Field(default_factory=list)
    evening_routine: list[RoutineStep] = Field(default_factory=list)
    recommended_ingredients: list[str] = Field(default_factory=list)
    avoid_ingredients: list[str] = Field(default_factory=list)

    @field_validator("morning_routine", "evening_routine", mode="before")
    @classmethod
    def _filter_routine_steps(cls, value: Any) -> list[Any]:
        if not isinstance(value, list):
            return []
        return [item for item in value if isinstance(item, dict)]

    @field_validator("recommended_ingredients", "avoid_ingredients", mode="before")
    @classmethod
    def _string_list(cls, value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item).strip() for item in value if item is not None and str(item).strip()]

    def morning_steps(self) -> list[dict]:
        return [step.model_dump() for step in self.morning_routine]

    def evening_steps(self) -> list[dict]:
        return [step.model_dump() for step in self.evening_routine]


class SkinAnalysisOutput(RoutineOutput):
    skin_type: str = "combination"
    problems: list[str] = Field(default_factory=list)
    confidence_score: float = 0.8
    skin_score: SkinScore | None = None

    @field_validator("problems", mode="before")
    @classmethod
    def _problems(cls, value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item).strip() for item in value if item is not None and str(item).strip()]

    @field_validator("confidence_score", mode="before")
    @classmethod
    def _confidence(cls, value: Any) -> float:
        return _clamp_number(value, 0.8, 0, 1)


class IngredientNote(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    benefit: str = ""
    reason: str = ""


class ProductScoreOutput(BaseModel):
    model_config = ConfigDict(extra="ignore")

    score: int = 50
    suitable: bool = True
    good_ingredients: list[IngredientNote] = Field(default_factory=list)
    neutral_ingredients: list[IngredientNote] = Field(default_factory=list)
    bad_ingredients: list[IngredientNote] = Field(default_factory=list)
    ph_comment: str = ""
    summary: str = ""

    @field_validator(
        "good_ingredients",
        "neutral_ingredients",
        "bad_ingredients",
        mode="before",
    )
    @classmethod
    def _ingredient_notes(cls, value: Any) -> list[Any]:
        if not isinstance(value, list):
            return []
        return [item for item in value if isinstance(item, dict) and item.get("name")]

    @field_validator("score", mode="before")
    @classmethod
    def _score(cls, value: Any) -> int:
        return int(_clamp_number(value, 50, 0, 100))


class ProductRecommendation(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    brand: str = ""
    why: str = ""
    key_ingredients: list[str] = Field(default_factory=list)
    price_range: str = ""
    time_of_use: str = "both"

    @field_validator("name", mode="before")
    @classmethod
    def _name(cls, value: Any) -> str:
        return str(value or "").strip()

    @field_validator("brand", "why", "price_range", mode="before")
    @classmethod
    def _string(cls, value: Any) -> str:
        return str(value or "").strip()

    @field_validator("key_ingredients", mode="before")
    @classmethod
    def _ingredients(cls, value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item).strip() for item in value if item is not None and str(item).strip()]

    @field_validator("time_of_use", mode="before")
    @classmethod
    def _time_of_use(cls, value: Any) -> str:
        value = str(value or "both").strip()
        return value if value in {"morning", "evening", "both"} else "both"


class ProductRecommendationsOutput(BaseModel):
    model_config = ConfigDict(extra="ignore")

    recommendations: list[ProductRecommendation] = Field(default_factory=list)

    @field_validator("recommendations", mode="before")
    @classmethod
    def _recommendations(cls, value: Any) -> list[Any]:
        if not isinstance(value, list):
            return []
        return [item for item in value if isinstance(item, dict) and str(item.get("name", "")).strip()]

    def as_dicts(self) -> list[dict]:
        return [recommendation.model_dump() for recommendation in self.recommendations]
