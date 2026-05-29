import unittest

from utils.database_url import normalize_async_database_url


class NormalizeAsyncDatabaseUrlTest(unittest.TestCase):
    def test_accepts_asyncpg_url(self):
        self.assertEqual(
            normalize_async_database_url("postgresql+asyncpg://u:p@host/db"),
            "postgresql+asyncpg://u:p@host/db",
        )

    def test_converts_postgresql_url(self):
        self.assertEqual(
            normalize_async_database_url("postgresql://u:p@host/db"),
            "postgresql+asyncpg://u:p@host/db",
        )

    def test_converts_legacy_postgres_url(self):
        self.assertEqual(
            normalize_async_database_url("postgres://u:p@host/db"),
            "postgresql+asyncpg://u:p@host/db",
        )


if __name__ == "__main__":
    unittest.main()
