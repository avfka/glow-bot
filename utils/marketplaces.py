from urllib.parse import quote_plus


def marketplace_search_urls(product_name: str) -> dict[str, str]:
    query = quote_plus(product_name.strip())
    if not query:
        return {}

    return {
        "wb": f"https://www.wildberries.ru/catalog/0/search.aspx?search={query}",
        "ozon": f"https://www.ozon.ru/search/?text={query}",
        "goldapple": f"https://goldapple.ru/search?query={query}",
    }


def merge_marketplace_urls(
    product_name: str,
    *,
    wb_url: str | None = None,
    za_url: str | None = None,
) -> dict[str, str]:
    urls = marketplace_search_urls(product_name)
    if wb_url:
        urls["wb"] = wb_url
    if za_url:
        urls["goldapple"] = za_url
    return urls
