"""Personal ingredient scoring against a user's skin profile."""
from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from database.models import IngredientsLibrary
from database.queries import get_ingredients_bulk


@dataclass
class IngredientEvaluation:
    name: str
    ru_name: str = ""
    verdict: str = "neutral"  # good / neutral / warning / bad
    reason: str = ""
    comedogenic_score: int = 0
    irritancy_score: int = 0


@dataclass
class ProductScoreResult:
    score: int
    suitable: bool
    good: list[IngredientEvaluation] = field(default_factory=list)
    neutral: list[IngredientEvaluation] = field(default_factory=list)
    warnings: list[IngredientEvaluation] = field(default_factory=list)
    bad: list[IngredientEvaluation] = field(default_factory=list)


async def score_product(
    session: AsyncSession,
    ingredients_parsed: list[str],
    profile: dict,
) -> ProductScoreResult:
    skin_type = profile.get("skin_type", "combination")
    problems = profile.get("skin_problems", [])
    allergies_raw = profile.get("allergies", "") or ""
    allergy_words = [a.strip().lower() for a in allergies_raw.split(",") if a.strip()]

    db_ingredients: list[IngredientsLibrary] = await get_ingredients_bulk(
        session, ingredients_parsed
    )
    db_map = {ing.inci_name.lower(): ing for ing in db_ingredients}

    good: list[IngredientEvaluation] = []
    neutral: list[IngredientEvaluation] = []
    warn: list[IngredientEvaluation] = []
    bad: list[IngredientEvaluation] = []

    penalty = 0
    bonus = 0

    for raw_name in ingredients_parsed:
        key = raw_name.lower()
        ing = db_map.get(key)

        # Check allergy
        if any(a in key for a in allergy_words):
            bad.append(IngredientEvaluation(
                name=raw_name,
                verdict="bad",
                reason="Совпадение с вашими аллергиями",
            ))
            penalty += 15
            continue

        if ing is None:
            neutral.append(IngredientEvaluation(name=raw_name, verdict="neutral"))
            continue

        avoid_for: list = ing.avoid_for or []
        safe_for: list = ing.safe_for or []

        is_avoid = skin_type in avoid_for or any(p in avoid_for for p in problems)
        is_safe = skin_type in safe_for or any(p in safe_for for p in problems)

        if is_avoid or (ing.comedogenic_score or 0) >= 4 or (ing.irritancy_score or 0) >= 4:
            bad.append(IngredientEvaluation(
                name=raw_name,
                ru_name=ing.ru_name or "",
                verdict="bad",
                reason=_build_reason(ing, skin_type, problems),
                comedogenic_score=ing.comedogenic_score or 0,
                irritancy_score=ing.irritancy_score or 0,
            ))
            penalty += 10
        elif (ing.comedogenic_score or 0) >= 2 or (ing.irritancy_score or 0) >= 2:
            warn.append(IngredientEvaluation(
                name=raw_name,
                ru_name=ing.ru_name or "",
                verdict="warning",
                reason=_build_reason(ing, skin_type, problems),
                comedogenic_score=ing.comedogenic_score or 0,
                irritancy_score=ing.irritancy_score or 0,
            ))
            penalty += 3
        elif is_safe:
            good.append(IngredientEvaluation(
                name=raw_name,
                ru_name=ing.ru_name or "",
                verdict="good",
                reason=(ing.description_simple or ""),
                comedogenic_score=ing.comedogenic_score or 0,
                irritancy_score=ing.irritancy_score or 0,
            ))
            bonus += 5
        else:
            neutral.append(IngredientEvaluation(
                name=raw_name,
                ru_name=ing.ru_name or "",
                verdict="neutral",
                comedogenic_score=ing.comedogenic_score or 0,
                irritancy_score=ing.irritancy_score or 0,
            ))

    base = 70
    score = max(0, min(100, base + bonus - penalty))
    suitable = score >= 50 and not bad

    return ProductScoreResult(
        score=score,
        suitable=suitable,
        good=good,
        neutral=neutral,
        warnings=warn,
        bad=bad,
    )


def _build_reason(ing: IngredientsLibrary, skin_type: str, problems: list[str]) -> str:
    parts = []
    if ing.description_simple:
        parts.append(ing.description_simple)
    if (ing.comedogenic_score or 0) >= 4:
        parts.append(f"комедогенность {ing.comedogenic_score}/5")
    if (ing.irritancy_score or 0) >= 4:
        parts.append(f"раздражающий {ing.irritancy_score}/5")
    avoid = ing.avoid_for or []
    if skin_type in avoid:
        parts.append(f"не рекомендуется для {skin_type} кожи")
    return "; ".join(parts) if parts else ""


def parse_ingredients_string(raw: str) -> list[str]:
    """Split raw INCI string into individual ingredient names."""
    ingredients = []
    for part in raw.replace("\n", ",").split(","):
        part = part.strip().strip(".")
        if part and len(part) > 1:
            ingredients.append(part)
    return ingredients
