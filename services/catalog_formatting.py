def format_commerce_line(
    *,
    price: int | None = None,
    rating: float | None = None,
    reviews_count: int | None = None,
) -> str:
    parts = []
    if price is not None:
        parts.append(f"Цена: {price} ₽")
    if rating is not None:
        rating_text = f"{rating:.1f}".rstrip("0").rstrip(".")
        if reviews_count is not None:
            parts.append(f"Рейтинг: {rating_text} ({reviews_count} отзывов)")
        else:
            parts.append(f"Рейтинг: {rating_text}")
    return " | ".join(parts)
