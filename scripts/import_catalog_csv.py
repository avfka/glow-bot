import argparse
import asyncio

from services.catalog_import import import_catalog_csv


async def main() -> None:
    parser = argparse.ArgumentParser(description="Import product catalog rows from CSV.")
    parser.add_argument("path", help="CSV path with name, brand, ingredients_raw and commerce fields")
    args = parser.parse_args()

    result = await import_catalog_csv(args.path)
    print(f"Imported: {result.imported}; skipped: {result.skipped}")


if __name__ == "__main__":
    asyncio.run(main())
