"""Product scan workflows."""
import logging
from dataclasses import dataclass, field
from typing import Any

from database import async_session_factory
from database.models import ProductCatalog
from database.repositories.products import (
    add_catalog_product,
    increment_scan_count,
    save_product_scan,
    search_catalog,
)
from database.repositories.profiles import get_latest_profile
from services.ingredient_scorer import (
    IngredientEvaluation,
    parse_ingredients_string,
    score_product,
)

logger = logging.getLogger(__name__)


@dataclass
class CatalogScanResult:
    product: ProductCatalog
    profile_exists: bool
    score: int | None = None
    suitable: bool | None = None
    good: list[IngredientEvaluation] = field(default_factory=list)
    neutral: list[IngredientEvaluation] = field(default_factory=list)
    warnings: list[IngredientEvaluation] = field(default_factory=list)
    bad: list[IngredientEvaluation] = field(default_factory=list)


@dataclass
class OcrScanResult:
    product_name: str
    ingredients_raw: str
    ingredients_list: list[str]
    profile_exists: bool
    score: int | None = None
    suitable: bool | None = None
    good: list[Any] = field(default_factory=list)
    neutral: list[Any] = field(default_factory=list)
    warnings: list[Any] = field(default_factory=list)
    bad: list[Any] = field(default_factory=list)
    ph_comment: str = ""


async def scan_catalog_product(
    *,
    user_id: int,
    query_text: str,
) -> CatalogScanResult | None:
    async with async_session_factory() as session:
        products = await search_catalog(session, query_text)

    if not products:
        return None

    product = products[0]
    async with async_session_factory() as session:
        await increment_scan_count(session, product.id, commit=False)
        profile = await get_latest_profile(session, user_id)
        await session.commit()

    if not product.ingredients_parsed or not profile:
        return CatalogScanResult(product=product, profile_exists=bool(profile))

    profile_dict = _profile_to_dict(profile)
    async with async_session_factory() as session:
        score_result = await score_product(
            session, product.ingredients_parsed, profile_dict
        )

    async with async_session_factory() as session:
        await save_product_scan(
            session=session,
            user_id=user_id,
            product_name=product.name,
            ingredients_raw=product.ingredients_raw or "",
            ingredients_parsed=product.ingredients_parsed or [],
            score=score_result.score,
            suitable=score_result.suitable,
            warnings=[
                {"name": warning.name, "reason": warning.reason}
                for warning in score_result.bad + score_result.warnings
            ],
            product_id=product.id,
            commit=False,
        )
        await session.commit()

    return CatalogScanResult(
        product=product,
        profile_exists=True,
        score=score_result.score,
        suitable=score_result.suitable,
        good=score_result.good,
        neutral=score_result.neutral,
        warnings=score_result.warnings,
        bad=score_result.bad,
    )


async def scan_ocr_ingredients(
    *,
    user_id: int,
    product_name: str,
    ingredients_raw: str,
    analyzer,
) -> OcrScanResult:
    ingredients_list = parse_ingredients_string(ingredients_raw)

    async with async_session_factory() as session:
        profile = await get_latest_profile(session, user_id)

    if not profile:
        await _save_ocr_catalog_product(
            user_id=user_id,
            product_name=product_name,
            ingredients_raw=ingredients_raw,
            ingredients_list=ingredients_list,
            score=0,
            suitable=True,
            save_scan=False,
        )
        return OcrScanResult(
            product_name=product_name,
            ingredients_raw=ingredients_raw,
            ingredients_list=ingredients_list,
            profile_exists=False,
        )

    profile_dict = _profile_to_dict(profile)
    async with async_session_factory() as session:
        score_result = await score_product(session, ingredients_list, profile_dict)

    good = score_result.good
    warnings = score_result.bad + score_result.warnings
    neutral = score_result.neutral
    score = score_result.score
    ph_comment = ""

    try:
        openai_result = await analyzer.score_product_for_profile(
            product_name=product_name,
            ingredients_list=ingredients_list,
            profile=profile_dict,
        )
        score = openai_result.get("score", score_result.score)
        good = [
            _note(
                name=item["name"],
                reason=item.get("benefit", ""),
            )
            for item in openai_result.get("good_ingredients", [])
        ]
        warnings = [
            _note(
                name=item["name"],
                reason=item.get("reason", ""),
            )
            for item in openai_result.get("bad_ingredients", [])
        ]
        neutral = [
            _note(name=item["name"])
            for item in openai_result.get("neutral_ingredients", [])
        ]
        ph_comment = openai_result.get("ph_comment", "")
    except Exception as exc:
        logger.warning("AI product scoring failed for user %s: %s", user_id, exc)

    suitable = score >= 50
    await _save_ocr_catalog_product(
        user_id=user_id,
        product_name=product_name,
        ingredients_raw=ingredients_raw,
        ingredients_list=ingredients_list,
        score=score,
        suitable=suitable,
        save_scan=True,
    )

    return OcrScanResult(
        product_name=product_name,
        ingredients_raw=ingredients_raw,
        ingredients_list=ingredients_list,
        profile_exists=True,
        score=score,
        suitable=suitable,
        good=good,
        neutral=neutral,
        warnings=warnings,
        ph_comment=ph_comment,
    )


async def _save_ocr_catalog_product(
    *,
    user_id: int,
    product_name: str,
    ingredients_raw: str,
    ingredients_list: list[str],
    score: int,
    suitable: bool,
    save_scan: bool,
) -> None:
    async with async_session_factory() as session:
        catalog_product = await add_catalog_product(
            session=session,
            name=product_name,
            brand=None,
            category="other",
            ingredients_raw=ingredients_raw,
            ingredients_parsed=ingredients_list,
            source="user_ocr",
            verified=False,
            commit=False,
        )
        if save_scan:
            await save_product_scan(
                session=session,
                user_id=user_id,
                product_name=product_name,
                ingredients_raw=ingredients_raw,
                ingredients_parsed=ingredients_list,
                score=score,
                suitable=suitable,
                warnings=[],
                product_id=catalog_product.id,
                commit=False,
            )
        await session.commit()


def _profile_to_dict(profile) -> dict:
    return {
        "skin_type": profile.skin_type,
        "skin_problems": profile.skin_problems or [],
        "allergies": profile.allergies,
    }


def _note(name: str, reason: str = ""):
    return type("", (), {"name": name, "reason": reason, "ru_name": ""})()
