import csv
from dataclasses import dataclass
from pathlib import Path

from database import async_session_factory
from database.repositories.products import upsert_catalog_product
from services.ingredient_scorer import parse_ingredients_string


@dataclass
class CatalogImportResult:
    imported: int = 0
    skipped: int = 0


def parse_int(value: str | None) -> int | None:
    if not value:
        return None
    digits = "".join(ch for ch in str(value) if ch.isdigit())
    return int(digits) if digits else None


def parse_float(value: str | None) -> float | None:
    if not value:
        return None
    normalized = str(value).replace(",", ".").strip()
    try:
        return float(normalized)
    except ValueError:
        return None


async def import_catalog_csv(path: str | Path) -> CatalogImportResult:
    result = CatalogImportResult()
    with Path(path).open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        async with async_session_factory() as session:
            for row in reader:
                name = (row.get("name") or "").strip()
                if not name:
                    result.skipped += 1
                    continue

                ingredients_raw = (row.get("ingredients_raw") or "").strip()
                await upsert_catalog_product(
                    session,
                    name=name,
                    brand=row.get("brand"),
                    category=row.get("category"),
                    ingredients_raw=ingredients_raw or None,
                    ingredients_parsed=parse_ingredients_string(ingredients_raw) if ingredients_raw else None,
                    source=row.get("source") or "csv_import",
                    verified=(row.get("verified") or "").strip().lower() in {"1", "true", "yes", "да"},
                    wb_url=row.get("wb_url"),
                    za_url=row.get("za_url"),
                    price=parse_int(row.get("price")),
                    rating=parse_float(row.get("rating")),
                    reviews_count=parse_int(row.get("reviews_count")),
                    review_summary=row.get("review_summary"),
                    commit=False,
                )
                result.imported += 1
            await session.commit()
    return result
