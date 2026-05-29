from datetime import datetime
from typing import Optional

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    IngredientsLibrary,
    ProductCatalog,
    ProductScan,
    UserProduct,
)
from database.repositories.common import finish_write, persist


async def get_active_products(session: AsyncSession, user_id: int) -> list[UserProduct]:
    result = await session.execute(
        select(UserProduct)
        .where(and_(UserProduct.user_id == user_id, UserProduct.status == "active"))
        .order_by(UserProduct.added_at.asc())
    )
    return result.scalars().all()


async def add_user_product(
    session: AsyncSession,
    user_id: int,
    product_name: str,
    product_type: str,
    time_of_use: str,
    *,
    commit: bool = True,
) -> UserProduct:
    product = UserProduct(
        user_id=user_id,
        product_name=product_name,
        product_type=product_type,
        time_of_use=time_of_use,
        status="active",
    )
    session.add(product)
    return await persist(session, product, commit)


async def remove_user_product(
    session: AsyncSession,
    product_id: int,
    user_id: int,
    *,
    commit: bool = True,
) -> bool:
    result = await session.execute(
        select(UserProduct).where(
            and_(UserProduct.id == product_id, UserProduct.user_id == user_id)
        )
    )
    product = result.scalar_one_or_none()
    if product:
        product.status = "removed"
        product.removed_at = datetime.utcnow()
        await finish_write(session, commit)
        return True
    return False


async def search_catalog(session: AsyncSession, query: str) -> list[ProductCatalog]:
    query = query.strip()
    if not query:
        return []

    pattern = f"%{query}%"
    result = await session.execute(
        select(ProductCatalog)
        .where(
            or_(
                ProductCatalog.name.ilike(pattern),
                ProductCatalog.brand.ilike(pattern),
            )
        )
        .limit(5)
    )
    return result.scalars().all()


async def get_catalog_product(
    session: AsyncSession, product_id: int
) -> Optional[ProductCatalog]:
    result = await session.execute(
        select(ProductCatalog).where(ProductCatalog.id == product_id)
    )
    return result.scalar_one_or_none()


async def add_catalog_product(
    session: AsyncSession,
    name: str,
    brand: Optional[str],
    category: str,
    ingredients_raw: str,
    ingredients_parsed: list,
    source: str = "user_ocr",
    verified: bool = False,
    *,
    commit: bool = True,
) -> ProductCatalog:
    product = ProductCatalog(
        name=name,
        brand=brand,
        category=category,
        ingredients_raw=ingredients_raw,
        ingredients_parsed=ingredients_parsed,
        source=source,
        verified=verified,
    )
    session.add(product)
    return await persist(session, product, commit)


async def upsert_catalog_product(
    session: AsyncSession,
    *,
    name: str,
    brand: Optional[str] = None,
    category: Optional[str] = None,
    ingredients_raw: Optional[str] = None,
    ingredients_parsed: Optional[list] = None,
    source: str = "import",
    verified: bool = False,
    wb_url: Optional[str] = None,
    za_url: Optional[str] = None,
    price: Optional[int] = None,
    rating: Optional[float] = None,
    reviews_count: Optional[int] = None,
    review_summary: Optional[str] = None,
    commit: bool = True,
) -> ProductCatalog:
    name = name.strip()
    brand = brand.strip() if brand else None
    za_url = za_url.strip() if za_url else None
    wb_url = wb_url.strip() if wb_url else None

    product = None
    if za_url:
        result = await session.execute(
            select(ProductCatalog).where(ProductCatalog.za_url == za_url)
        )
        product = result.scalar_one_or_none()

    if product is None and brand:
        result = await session.execute(
            select(ProductCatalog).where(
                and_(
                    func.lower(ProductCatalog.name) == name.lower(),
                    func.lower(ProductCatalog.brand) == brand.lower(),
                )
            )
        )
        product = result.scalar_one_or_none()

    if product is None:
        product = ProductCatalog(name=name)
        session.add(product)

    product.brand = brand or product.brand
    product.category = category or product.category
    product.ingredients_raw = ingredients_raw or product.ingredients_raw
    product.ingredients_parsed = ingredients_parsed or product.ingredients_parsed
    product.source = source or product.source
    product.verified = verified
    product.wb_url = wb_url or product.wb_url
    product.za_url = za_url or product.za_url
    product.price = price if price is not None else product.price
    product.rating = rating if rating is not None else product.rating
    product.reviews_count = reviews_count if reviews_count is not None else product.reviews_count
    product.review_summary = review_summary or product.review_summary

    return await persist(session, product, commit)


async def increment_scan_count(
    session: AsyncSession,
    product_id: int,
    *,
    commit: bool = True,
) -> None:
    result = await session.execute(
        select(ProductCatalog).where(ProductCatalog.id == product_id)
    )
    product = result.scalar_one_or_none()
    if product:
        product.scan_count = (product.scan_count or 0) + 1
        await finish_write(session, commit)


async def get_ingredient_by_inci(
    session: AsyncSession, inci_name: str
) -> Optional[IngredientsLibrary]:
    result = await session.execute(
        select(IngredientsLibrary).where(IngredientsLibrary.inci_name.ilike(inci_name))
    )
    return result.scalar_one_or_none()


async def get_ingredients_bulk(
    session: AsyncSession, inci_names: list[str]
) -> list[IngredientsLibrary]:
    result = await session.execute(
        select(IngredientsLibrary).where(IngredientsLibrary.inci_name.in_(inci_names))
    )
    return result.scalars().all()


async def save_product_scan(
    session: AsyncSession,
    user_id: int,
    product_name: str,
    ingredients_raw: str,
    ingredients_parsed: list,
    score: int,
    suitable: bool,
    warnings: list,
    product_id: Optional[int] = None,
    *,
    commit: bool = True,
) -> ProductScan:
    scan = ProductScan(
        user_id=user_id,
        product_id=product_id,
        product_name=product_name,
        ingredients_raw=ingredients_raw,
        ingredients_parsed=ingredients_parsed,
        score=score,
        suitable=suitable,
        warnings=warnings,
    )
    session.add(scan)
    return await persist(session, scan, commit)


async def get_user_scans(session: AsyncSession, user_id: int) -> list[ProductScan]:
    result = await session.execute(
        select(ProductScan)
        .where(ProductScan.user_id == user_id)
        .order_by(ProductScan.created_at.desc())
        .limit(10)
    )
    return result.scalars().all()
