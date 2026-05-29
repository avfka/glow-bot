"""AI product recommendation workflow."""
import json

from services.ai_schemas import ProductRecommendationsOutput

SKIN_TYPE_RU = {
    "oily": "жирная",
    "dry": "сухая",
    "combination": "комбинированная",
    "sensitive": "чувствительная",
}
BUDGET_RU = {"low": "до 500 ₽", "medium": "500-2000 ₽", "high": "от 2000 ₽"}
GOAL_RU = {
    "hydration": "увлажнение",
    "tone": "выравнивание тона",
    "anti-age": "антивозрастной",
}


async def get_product_recommendations(
    profile,
    *,
    category_label: str,
) -> list[dict]:
    """Ask AI for product recommendations and return validated dictionaries."""
    from config import settings
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "Ты - косметолог. Рекомендуй реальные продукты. "
                    "Отвечай только JSON."
                ),
            },
            {"role": "user", "content": build_recommendation_prompt(profile, category_label)},
        ],
        response_format={"type": "json_object"},
        max_tokens=1000,
    )

    data = json.loads(response.choices[0].message.content)
    validated = ProductRecommendationsOutput.model_validate(data)
    return validated.as_dicts()


def build_recommendation_prompt(profile, category_label: str) -> str:
    skin_type = SKIN_TYPE_RU.get(profile.skin_type or "combination", profile.skin_type)
    problems = ", ".join(profile.skin_problems or []) or "нет"
    budget = BUDGET_RU.get(profile.budget or "medium", profile.budget)
    goal = GOAL_RU.get(profile.goal or "hydration", profile.goal)
    allergies = profile.allergies or "нет"

    return (
        f"Порекомендуй 4 реальных продукта категории «{category_label}» для:\n"
        f"Тип кожи: {skin_type}\n"
        f"Проблемы: {problems}\n"
        f"Цель: {goal}\n"
        f"Бюджет: {budget}\n"
        f"Аллергии: {allergies}\n\n"
        "Только реальные бренды, доступные в России (La Roche-Posay, The Ordinary, Виши, "
        "Bioderma, Garnier, CeraVe, Eucerin, Clinique и т.д.).\n\n"
        "Ответь JSON:\n"
        '{"recommendations": ['
        '{"name": "...", "brand": "...", "why": "почему подходит 1-2 предложения", '
        '"key_ingredients": ["ингредиент1", "ингредиент2"], '
        '"price_range": "от XXX ₽", "time_of_use": "morning|evening|both"}'
        "]}"
    )
