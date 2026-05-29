import os
from functools import lru_cache

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from utils.database_url import normalize_async_database_url

load_dotenv()

def _database_url() -> str:
    return normalize_async_database_url(os.environ["DATABASE_URL"])


@lru_cache(maxsize=1)
def get_engine():
    return create_async_engine(_database_url(), echo=False, pool_pre_ping=True)


@lru_cache(maxsize=1)
def get_sessionmaker():
    return async_sessionmaker(
        get_engine(),
        expire_on_commit=False,
        class_=AsyncSession,
    )


def async_session_factory() -> AsyncSession:
    return get_sessionmaker()()


async def get_session() -> AsyncSession:
    async with async_session_factory() as session:
        yield session
