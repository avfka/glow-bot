import base64
import json
import logging
from typing import Optional

from openai import AsyncOpenAI

from config import settings
from services.ai_schemas import ProductScoreOutput, RoutineOutput, SkinAnalysisOutput
from services.skin_analyzer import SkinAnalyzer, SkinAnalysisResult

logger = logging.getLogger(__name__)

SKIN_TYPE_RU = {
    "oily": "жирная",
    "dry": "сухая",
    "combination": "комбинированная",
    "sensitive": "чувствительная",
}

BUDGET_RU = {
    "low": "бюджетный (до 500 руб.)",
    "medium": "средний (500–2000 руб.)",
    "high": "премиум (от 2000 руб.)",
}

GOAL_RU = {
    "hydration": "увлажнение",
    "tone": "выравнивание тона",
    "anti-age": "антивозрастной уход",
}


class OpenAIAnalyzer(SkinAnalyzer):
    def __init__(self) -> None:
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.vision_model = settings.openai_vision_model

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
        profile_text = (
            f"Тип кожи: {SKIN_TYPE_RU.get(skin_type, skin_type)}\n"
            f"Проблемы: {', '.join(problems) if problems else 'не указаны'}\n"
            f"Аллергии: {allergies or 'нет'}\n"
            f"Бюджет: {BUDGET_RU.get(budget, budget)}\n"
            f"Цель: {GOAL_RU.get(goal, goal)}\n"
            f"Возраст: {age} лет"
        )

        system_prompt = (
            "Ты — профессиональный косметолог-аналитик. "
            "Анализируй кожу по фото и анкете. "
            "Отвечай ТОЛЬКО в формате JSON без лишнего текста."
        )

        json_schema = """{
  "skin_type": "oily|dry|combination|sensitive",
  "problems": ["список обнаруженных проблем"],
  "recommended_ingredients": ["список рекомендуемых ингредиентов INCI"],
  "avoid_ingredients": ["список ингредиентов для избегания INCI"],
  "morning_routine": [
    {"step": 1, "name": "название шага", "description": "описание", "product_type": "тип продукта"}
  ],
  "evening_routine": [
    {"step": 1, "name": "название шага", "description": "описание", "product_type": "тип продукта"}
  ],
  "confidence_score": 0.85,
  "skin_score": {"overall": 70, "hydration": 60, "evenness": 75, "pores": 65}
}"""

        user_content: list = [
            {
                "type": "text",
                "text": (
                    f"Анкета пользователя:\n{profile_text}\n\n"
                    f"Проанализируй {'фото кожи и ' if photo_base64 else ''}"
                    f"анкету. Верни JSON по схеме:\n{json_schema}"
                ),
            }
        ]

        if photo_base64:
            user_content.insert(0, {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{photo_base64}", "detail": "high"},
            })

        response = await self.client.chat.completions.create(
            model=self.vision_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            response_format={"type": "json_object"},
            max_tokens=2000,
        )

        raw = response.choices[0].message.content
        data = json.loads(raw)
        validated = SkinAnalysisOutput.model_validate(data)
        raw_response = validated.model_dump()

        return SkinAnalysisResult(
            skin_type=validated.skin_type or skin_type,
            problems=validated.problems or problems,
            recommended_ingredients=validated.recommended_ingredients,
            avoid_ingredients=validated.avoid_ingredients,
            morning_routine=validated.morning_steps(),
            evening_routine=validated.evening_steps(),
            confidence_score=validated.confidence_score,
            raw_response=raw_response,
        )

    async def generate_routine(
        self,
        profile: dict,
        user_products: list[dict],
    ) -> SkinAnalysisResult:
        products_text = ""
        if user_products:
            products_text = "\n\nПродукты пользователя:\n" + "\n".join(
                f"- {p['product_name']} ({p['product_type']}, {p['time_of_use']})"
                for p in user_products
            )

        skin_type = profile.get("skin_type", "combination")
        problems = profile.get("skin_problems", [])
        allergies = profile.get("allergies", "")
        budget = profile.get("budget", "medium")
        goal = profile.get("goal", "hydration")
        age = profile.get("age", 25)

        profile_text = (
            f"Тип кожи: {SKIN_TYPE_RU.get(skin_type, skin_type)}\n"
            f"Проблемы: {', '.join(problems) if problems else 'нет'}\n"
            f"Аллергии: {allergies or 'нет'}\n"
            f"Бюджет: {BUDGET_RU.get(budget, budget)}\n"
            f"Цель: {GOAL_RU.get(goal, goal)}\n"
            f"Возраст: {age} лет"
            f"{products_text}"
        )

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты — профессиональный косметолог. Составляй персональные рутины ухода. "
                        "Если у пользователя есть продукты — включи их в рутину. "
                        "Отвечай ТОЛЬКО в формате JSON."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Составь рутину ухода для профиля:\n{profile_text}\n\n"
                        "Формат:\n"
                        '{"morning_routine": [{"step": 1, "name": "...", "description": "...", "product_type": "..."}], '
                        '"evening_routine": [{"step": 1, "name": "...", "description": "...", "product_type": "..."}], '
                        '"recommended_ingredients": [], "avoid_ingredients": []}'
                    ),
                },
            ],
            response_format={"type": "json_object"},
            max_tokens=1500,
        )

        data = json.loads(response.choices[0].message.content)
        validated = RoutineOutput.model_validate(data)
        return SkinAnalysisResult(
            skin_type=skin_type,
            problems=problems,
            recommended_ingredients=validated.recommended_ingredients,
            avoid_ingredients=validated.avoid_ingredients,
            morning_routine=validated.morning_steps(),
            evening_routine=validated.evening_steps(),
            confidence_score=1.0,
            raw_response=validated.model_dump(),
        )

    async def extract_ingredients_from_image(self, photo_base64: str) -> str:
        response = await self.client.chat.completions.create(
            model=self.vision_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты — эксперт по косметическим ингредиентам. "
                        "Извлекай INCI-список ингредиентов с фото этикетки."
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{photo_base64}",
                                "detail": "high",
                            },
                        },
                        {
                            "type": "text",
                            "text": (
                                "Прочитай состав продукта на этикетке. "
                                "Верни ТОЛЬКО список ингредиентов через запятую "
                                "в формате INCI (латиница), как написано на упаковке. "
                                "Ничего больше не добавляй."
                            ),
                        },
                    ],
                },
            ],
            max_tokens=500,
        )
        return response.choices[0].message.content.strip()

    async def score_product_for_profile(
        self,
        product_name: str,
        ingredients_list: list[str],
        profile: dict,
    ) -> dict:
        skin_type = profile.get("skin_type", "combination")
        problems = profile.get("skin_problems", [])
        allergies = profile.get("allergies", "")

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты — косметолог-аналитик. Оцениваешь состав продукта "
                        "под конкретный профиль кожи. Отвечай ТОЛЬКО в JSON."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Продукт: {product_name}\n"
                        f"Ингредиенты: {', '.join(ingredients_list)}\n\n"
                        f"Профиль:\n"
                        f"Тип кожи: {SKIN_TYPE_RU.get(skin_type, skin_type)}\n"
                        f"Проблемы: {', '.join(problems)}\n"
                        f"Аллергии: {allergies or 'нет'}\n\n"
                        "Оцени продукт. Формат:\n"
                        '{"score": 75, "suitable": true, '
                        '"good_ingredients": [{"name": "...", "benefit": "..."}], '
                        '"neutral_ingredients": [{"name": "..."}], '
                        '"bad_ingredients": [{"name": "...", "reason": "..."}], '
                        '"ph_comment": "...", "summary": "..."}'
                    ),
                },
            ],
            response_format={"type": "json_object"},
            max_tokens=800,
        )
        data = json.loads(response.choices[0].message.content)
        return ProductScoreOutput.model_validate(data).model_dump()
